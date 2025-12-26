# utils/supply_chain_gap/calculator.py

"""
Calculator for Supply Chain GAP Analysis
Performs full multi-level GAP calculation: FG + Raw Materials
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .constants import THRESHOLDS, STATUS_CONFIG, ACTION_TYPES
from .result import SupplyChainGAPResult, CustomerImpact, ActionRecommendation

logger = logging.getLogger(__name__)


class SupplyChainGAPCalculator:
    """
    Calculator for Supply Chain GAP Analysis.
    
    Performs:
    1. FG GAP calculation (supply vs demand)
    2. Product classification (manufacturing vs trading)
    3. BOM explosion for manufacturing products
    4. Raw material GAP calculation
    5. Action recommendations
    """
    
    def __init__(self):
        pass
    
    def calculate(
        self,
        # FG Data
        fg_supply_df: pd.DataFrame,
        fg_demand_df: pd.DataFrame,
        fg_safety_stock_df: Optional[pd.DataFrame] = None,
        
        # Classification & BOM
        classification_df: Optional[pd.DataFrame] = None,
        bom_explosion_df: Optional[pd.DataFrame] = None,
        existing_mo_demand_df: Optional[pd.DataFrame] = None,
        
        # Raw Material Data
        raw_supply_df: Optional[pd.DataFrame] = None,
        raw_safety_stock_df: Optional[pd.DataFrame] = None,
        
        # Options
        selected_supply_sources: Optional[List[str]] = None,
        selected_demand_sources: Optional[List[str]] = None,
        include_fg_safety: bool = True,
        include_raw_safety: bool = True,
        include_alternatives: bool = True,
        include_existing_mo: bool = True
    ) -> SupplyChainGAPResult:
        """
        Perform full Supply Chain GAP calculation.
        
        Returns:
            SupplyChainGAPResult with all analysis data
        """
        logger.info("Starting Supply Chain GAP calculation")
        
        result = SupplyChainGAPResult(
            timestamp=datetime.now(),
            filters_used={
                'supply_sources': selected_supply_sources,
                'demand_sources': selected_demand_sources,
                'include_fg_safety': include_fg_safety,
                'include_raw_safety': include_raw_safety
            }
        )
        
        # =====================================================================
        # LEVEL 1: FG GAP
        # =====================================================================
        logger.info("Level 1: Calculating FG GAP...")
        
        fg_gap_df, fg_metrics, customer_impact = self._calculate_fg_gap(
            supply_df=fg_supply_df,
            demand_df=fg_demand_df,
            safety_stock_df=fg_safety_stock_df,
            selected_supply_sources=selected_supply_sources,
            selected_demand_sources=selected_demand_sources,
            include_safety=include_fg_safety
        )
        
        result.fg_gap_df = fg_gap_df
        result.fg_metrics = fg_metrics
        result.customer_impact = customer_impact
        
        logger.info(f"FG GAP: {len(fg_gap_df)} products, {fg_metrics.get('shortage_count', 0)} shortages")
        
        # =====================================================================
        # CLASSIFICATION
        # =====================================================================
        if classification_df is not None and not classification_df.empty:
            logger.info("Classifying products (Manufacturing vs Trading)...")
            
            result.classification_df = classification_df
            result.manufacturing_df = classification_df[classification_df['has_bom'] == 1].copy()
            result.trading_df = classification_df[classification_df['has_bom'] == 0].copy()
            
            logger.info(f"Classification: {len(result.manufacturing_df)} MFG, {len(result.trading_df)} Trading")
        
        # =====================================================================
        # LEVEL 2: RAW MATERIAL GAP (for manufacturing products with shortage)
        # =====================================================================
        if (bom_explosion_df is not None and not bom_explosion_df.empty and
            raw_supply_df is not None and not raw_supply_df.empty):
            
            logger.info("Level 2: Calculating Raw Material GAP...")
            
            # Get manufacturing products with shortage
            mfg_shortage = result.get_manufacturing_shortage()
            
            if not mfg_shortage.empty:
                mfg_product_ids = mfg_shortage['product_id'].tolist()
                
                # Filter BOM for shortage products
                id_col = 'output_product_id' if 'output_product_id' in bom_explosion_df.columns else 'fg_product_id'
                filtered_bom = bom_explosion_df[bom_explosion_df[id_col].isin(mfg_product_ids)].copy()
                
                result.bom_explosion_df = filtered_bom
                
                # Calculate raw material demand from BOM explosion
                raw_demand_df = self._calculate_raw_demand(
                    fg_shortage_df=mfg_shortage,
                    bom_explosion_df=filtered_bom,
                    existing_mo_demand_df=existing_mo_demand_df if include_existing_mo else None
                )
                result.raw_demand_df = raw_demand_df
                
                # Calculate raw material GAP
                raw_gap_df, raw_metrics, alt_analysis = self._calculate_raw_gap(
                    raw_demand_df=raw_demand_df,
                    raw_supply_df=raw_supply_df,
                    raw_safety_stock_df=raw_safety_stock_df if include_raw_safety else None,
                    include_alternatives=include_alternatives
                )
                
                result.raw_supply_df = raw_supply_df
                result.raw_gap_df = raw_gap_df
                result.raw_metrics = raw_metrics
                result.alternative_analysis_df = alt_analysis
                
                logger.info(f"Raw GAP: {len(raw_gap_df)} materials, {raw_metrics.get('shortage_count', 0)} shortages")
        
        # =====================================================================
        # ACTION RECOMMENDATIONS
        # =====================================================================
        logger.info("Generating action recommendations...")
        
        mo_suggestions, po_fg_suggestions, po_raw_suggestions = self._generate_actions(result)
        
        result.mo_suggestions = mo_suggestions
        result.po_fg_suggestions = po_fg_suggestions
        result.po_raw_suggestions = po_raw_suggestions
        
        logger.info(f"Actions: {len(mo_suggestions)} MO, {len(po_fg_suggestions)} PO-FG, {len(po_raw_suggestions)} PO-Raw")
        
        return result
    
    # =========================================================================
    # LEVEL 1: FG GAP CALCULATION
    # =========================================================================
    
    def _calculate_fg_gap(
        self,
        supply_df: pd.DataFrame,
        demand_df: pd.DataFrame,
        safety_stock_df: Optional[pd.DataFrame],
        selected_supply_sources: Optional[List[str]],
        selected_demand_sources: Optional[List[str]],
        include_safety: bool
    ) -> Tuple[pd.DataFrame, Dict[str, Any], CustomerImpact]:
        """Calculate FG GAP"""
        
        # Filter by sources
        if selected_supply_sources and not supply_df.empty:
            supply_df = supply_df[supply_df['supply_source'].isin(selected_supply_sources)]
        
        if selected_demand_sources and not demand_df.empty:
            demand_df = demand_df[demand_df['demand_source'].isin(selected_demand_sources)]
        
        # Aggregate supply by product
        if supply_df.empty:
            supply_agg = pd.DataFrame(columns=['product_id', 'total_supply'])
        else:
            supply_agg = supply_df.groupby('product_id').agg({
                'available_quantity': 'sum',
                'product_name': 'first',
                'pt_code': 'first',
                'brand': 'first',
                'standard_uom': 'first',
                'unit_cost_usd': 'mean'
            }).reset_index()
            supply_agg.rename(columns={'available_quantity': 'total_supply'}, inplace=True)
            
            # Add supply by source
            if 'supply_source' in supply_df.columns:
                for source in ['INVENTORY', 'CAN_PENDING', 'WAREHOUSE_TRANSFER', 'PURCHASE_ORDER']:
                    source_sum = supply_df[supply_df['supply_source'] == source].groupby('product_id')['available_quantity'].sum()
                    supply_agg[f'supply_{source.lower()}'] = supply_agg['product_id'].map(source_sum).fillna(0)
        
        # Aggregate demand by product
        if demand_df.empty:
            demand_agg = pd.DataFrame(columns=['product_id', 'total_demand'])
        else:
            demand_agg = demand_df.groupby('product_id').agg({
                'required_quantity': 'sum',
                'product_name': 'first',
                'pt_code': 'first',
                'brand': 'first',
                'standard_uom': 'first',
                'selling_unit_price': 'mean',
                'customer': lambda x: x.nunique()
            }).reset_index()
            demand_agg.rename(columns={
                'required_quantity': 'total_demand',
                'customer': 'customer_count'
            }, inplace=True)
            
            # Add demand by source
            if 'demand_source' in demand_df.columns:
                for source in ['OC_PENDING', 'FORECAST']:
                    source_sum = demand_df[demand_df['demand_source'] == source].groupby('product_id')['required_quantity'].sum()
                    demand_agg[f'demand_{source.lower()}'] = demand_agg['product_id'].map(source_sum).fillna(0)
        
        # Merge supply and demand
        all_products = set(supply_agg['product_id'].tolist() if not supply_agg.empty else []) | \
                       set(demand_agg['product_id'].tolist() if not demand_agg.empty else [])
        
        if not all_products:
            return pd.DataFrame(), {}, CustomerImpact()
        
        gap_df = pd.DataFrame({'product_id': list(all_products)})
        
        if not supply_agg.empty:
            gap_df = gap_df.merge(supply_agg, on='product_id', how='left')
        
        if not demand_agg.empty:
            gap_df = gap_df.merge(demand_agg, on='product_id', how='left', suffixes=('', '_demand'))
            # Clean up duplicate columns
            for col in ['product_name', 'pt_code', 'brand', 'standard_uom']:
                if f'{col}_demand' in gap_df.columns:
                    gap_df[col] = gap_df[col].fillna(gap_df[f'{col}_demand'])
                    gap_df.drop(columns=[f'{col}_demand'], inplace=True)
        
        # Fill NaN
        gap_df['total_supply'] = gap_df['total_supply'].fillna(0) if 'total_supply' in gap_df.columns else 0
        gap_df['total_demand'] = gap_df['total_demand'].fillna(0) if 'total_demand' in gap_df.columns else 0
        
        # Add safety stock
        if include_safety and safety_stock_df is not None and not safety_stock_df.empty:
            gap_df = gap_df.merge(
                safety_stock_df[['product_id', 'safety_stock_qty', 'reorder_point']],
                on='product_id',
                how='left'
            )
            gap_df['safety_stock_qty'] = gap_df['safety_stock_qty'].fillna(0) if 'safety_stock_qty' in gap_df.columns else 0
        else:
            gap_df['safety_stock_qty'] = 0
        
        # Calculate GAP
        gap_df['safety_gap'] = gap_df['total_supply'] - gap_df['safety_stock_qty']
        gap_df['available_supply'] = gap_df['safety_gap'].clip(lower=0)
        gap_df['net_gap'] = gap_df['available_supply'] - gap_df['total_demand']
        gap_df['true_gap'] = gap_df['total_supply'] - gap_df['total_demand']
        
        # Coverage ratio
        gap_df['coverage_ratio'] = np.where(
            gap_df['total_demand'] > 0,
            gap_df['available_supply'] / gap_df['total_demand'],
            np.where(gap_df['total_supply'] > 0, 999, 0)
        )
        
        # Classify status
        gap_df['gap_status'] = gap_df.apply(self._classify_gap_status, axis=1)
        gap_df['gap_group'] = gap_df['gap_status'].apply(self._get_gap_group)
        gap_df['priority'] = gap_df['gap_status'].apply(lambda x: STATUS_CONFIG.get(x, {}).get('priority', 99))
        
        # At risk value
        selling_price = gap_df['selling_unit_price'].fillna(0) if 'selling_unit_price' in gap_df.columns else 0
        gap_df['at_risk_value'] = np.where(
            gap_df['net_gap'] < 0,
            abs(gap_df['net_gap']) * selling_price,
            0
        )
        
        # Sort by priority
        gap_df = gap_df.sort_values(['priority', 'net_gap']).reset_index(drop=True)
        
        # Calculate metrics
        metrics = self._calculate_fg_metrics(gap_df)
        
        # Customer impact
        customer_impact = self._calculate_customer_impact(demand_df, gap_df)
        
        return gap_df, metrics, customer_impact
    
    def _classify_gap_status(self, row) -> str:
        """Classify GAP status based on net_gap sign and coverage"""
        net_gap = row.get('net_gap', 0)
        total_demand = row.get('total_demand', 0)
        total_supply = row.get('total_supply', 0)
        coverage = row.get('coverage_ratio', 0)
        
        # No activity cases
        if total_demand == 0 and total_supply == 0:
            return 'NO_ACTIVITY'
        if total_demand == 0:
            return 'NO_DEMAND'
        
        # Shortage
        if net_gap < 0:
            if coverage < THRESHOLDS['shortage']['critical']:
                return 'CRITICAL_SHORTAGE'
            elif coverage < THRESHOLDS['shortage']['severe']:
                return 'SEVERE_SHORTAGE'
            elif coverage < THRESHOLDS['shortage']['high']:
                return 'HIGH_SHORTAGE'
            elif coverage < THRESHOLDS['shortage']['moderate']:
                return 'MODERATE_SHORTAGE'
            else:
                return 'LIGHT_SHORTAGE'
        
        # Balanced
        if net_gap == 0:
            return 'BALANCED'
        
        # Surplus
        if coverage <= THRESHOLDS['surplus']['light']:
            return 'LIGHT_SURPLUS'
        elif coverage <= THRESHOLDS['surplus']['moderate']:
            return 'MODERATE_SURPLUS'
        elif coverage <= THRESHOLDS['surplus']['high']:
            return 'HIGH_SURPLUS'
        else:
            return 'SEVERE_SURPLUS'
    
    def _get_gap_group(self, status: str) -> str:
        """Get GAP group from status"""
        if 'SHORTAGE' in status:
            return 'SHORTAGE'
        elif status == 'BALANCED':
            return 'OPTIMAL'
        elif 'SURPLUS' in status:
            return 'SURPLUS'
        else:
            return 'INACTIVE'
    
    def _calculate_fg_metrics(self, gap_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate FG metrics"""
        if gap_df.empty:
            return {}
        
        return {
            'total_items': len(gap_df),
            'shortage_count': len(gap_df[gap_df['net_gap'] < 0]),
            'surplus_count': len(gap_df[gap_df['net_gap'] > 0]),
            'balanced_count': len(gap_df[gap_df['net_gap'] == 0]),
            'at_risk_value': gap_df['at_risk_value'].sum(),
            'total_supply': gap_df['total_supply'].sum(),
            'total_demand': gap_df['total_demand'].sum()
        }
    
    def _calculate_customer_impact(
        self,
        demand_df: pd.DataFrame,
        gap_df: pd.DataFrame
    ) -> CustomerImpact:
        """Calculate customer impact from shortages"""
        if demand_df.empty or gap_df.empty:
            return CustomerImpact()
        
        shortage_products = gap_df[gap_df['net_gap'] < 0]['product_id'].tolist()
        
        if not shortage_products:
            return CustomerImpact()
        
        affected_demand = demand_df[demand_df['product_id'].isin(shortage_products)]
        
        if affected_demand.empty or 'customer' not in affected_demand.columns:
            return CustomerImpact()
        
        affected_customers = affected_demand['customer'].dropna().unique().tolist()
        at_risk_value = gap_df[gap_df['net_gap'] < 0]['at_risk_value'].sum()
        
        return CustomerImpact(
            affected_count=len(affected_customers),
            affected_customers=affected_customers,
            at_risk_value=at_risk_value
        )
    
    # =========================================================================
    # LEVEL 2: RAW MATERIAL GAP CALCULATION
    # =========================================================================
    
    def _calculate_raw_demand(
        self,
        fg_shortage_df: pd.DataFrame,
        bom_explosion_df: pd.DataFrame,
        existing_mo_demand_df: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """Calculate raw material demand from FG shortage + BOM explosion"""
        
        if fg_shortage_df.empty or bom_explosion_df.empty:
            return pd.DataFrame()
        
        # Identify the FG product ID column
        id_col = 'output_product_id' if 'output_product_id' in bom_explosion_df.columns else 'fg_product_id'
        
        # Merge shortage with BOM
        merged = bom_explosion_df.merge(
            fg_shortage_df[['product_id', 'net_gap']].rename(columns={'product_id': id_col, 'net_gap': 'fg_shortage'}),
            on=id_col,
            how='inner'
        )
        
        if merged.empty:
            return pd.DataFrame()
        
        # Calculate required quantity
        # required_qty = (fg_shortage / output_qty) * quantity_per_output * (1 + scrap_rate/100)
        merged['fg_shortage'] = merged['fg_shortage'].abs()
        merged['bom_output_quantity'] = merged['bom_output_quantity'].fillna(1).replace(0, 1) if 'bom_output_quantity' in merged.columns else 1
        merged['quantity_per_output'] = merged['quantity_per_output'].fillna(1) if 'quantity_per_output' in merged.columns else 1
        merged['scrap_rate'] = merged['scrap_rate'].fillna(0) if 'scrap_rate' in merged.columns else 0
        
        merged['required_qty'] = (
            (merged['fg_shortage'] / merged['bom_output_quantity']) *
            merged['quantity_per_output'] *
            (1 + merged['scrap_rate'] / 100)
        )
        
        # Build aggregation dict with only existing columns
        agg_cols = {
            'required_qty': 'sum',
            id_col: 'nunique'
        }
        
        # Add optional columns if they exist
        optional_cols = {
            'material_pt_code': 'first',
            'material_name': 'first',
            'material_brand': 'first',
            'material_uom': 'first',
            'material_type': 'first',
            'is_primary': 'first',
            'alternative_priority': 'first',
            'primary_material_id': 'first'
        }
        
        for col, agg_func in optional_cols.items():
            if col in merged.columns:
                agg_cols[col] = agg_func
        
        raw_demand = merged.groupby('material_id').agg(agg_cols).reset_index()
        raw_demand.rename(columns={id_col: 'fg_product_count'}, inplace=True)
        
        # Add existing MO demand
        if existing_mo_demand_df is not None and not existing_mo_demand_df.empty:
            mo_demand = existing_mo_demand_df.groupby('material_id')['pending_qty'].sum().reset_index()
            mo_demand.rename(columns={'pending_qty': 'existing_mo_demand'}, inplace=True)
            
            raw_demand = raw_demand.merge(mo_demand, on='material_id', how='left')
            raw_demand['existing_mo_demand'] = raw_demand['existing_mo_demand'].fillna(0) if 'existing_mo_demand' in raw_demand.columns else 0
            raw_demand['total_required_qty'] = raw_demand['required_qty'] + raw_demand['existing_mo_demand']
        else:
            raw_demand['existing_mo_demand'] = 0
            raw_demand['total_required_qty'] = raw_demand['required_qty']
        
        return raw_demand
    
    def _calculate_raw_gap(
        self,
        raw_demand_df: pd.DataFrame,
        raw_supply_df: pd.DataFrame,
        raw_safety_stock_df: Optional[pd.DataFrame],
        include_alternatives: bool
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        """Calculate raw material GAP"""
        
        if raw_demand_df.empty:
            return pd.DataFrame(), {}, pd.DataFrame()
        
        # Aggregate supply by material
        # Note: raw_supply_df comes from raw_material_supply_summary_view which already has total_supply
        if raw_supply_df.empty:
            supply_agg = pd.DataFrame(columns=['material_id', 'total_supply'])
        else:
            # Check which column to use for aggregation
            if 'total_supply' in raw_supply_df.columns:
                # Already aggregated (from summary view)
                supply_agg = raw_supply_df[['material_id', 'total_supply']].copy()
                # Group in case of duplicates
                supply_agg = supply_agg.groupby('material_id')['total_supply'].sum().reset_index()
            elif 'available_quantity' in raw_supply_df.columns:
                # Detail view - need to aggregate
                supply_agg = raw_supply_df.groupby('material_id').agg({
                    'available_quantity': 'sum'
                }).reset_index()
                supply_agg.rename(columns={'available_quantity': 'total_supply'}, inplace=True)
            else:
                # Fallback - empty
                supply_agg = pd.DataFrame(columns=['material_id', 'total_supply'])
        
        # Merge demand with supply
        raw_gap = raw_demand_df.merge(supply_agg, on='material_id', how='left')
        raw_gap['total_supply'] = raw_gap['total_supply'].fillna(0) if 'total_supply' in raw_gap.columns else 0
        
        # Add safety stock
        if raw_safety_stock_df is not None and not raw_safety_stock_df.empty:
            raw_gap = raw_gap.merge(
                raw_safety_stock_df[['material_id', 'safety_stock_qty']],
                on='material_id',
                how='left'
            )
            raw_gap['safety_stock_qty'] = raw_gap['safety_stock_qty'].fillna(0) if 'safety_stock_qty' in raw_gap.columns else 0
        else:
            raw_gap['safety_stock_qty'] = 0
        
        # Calculate GAP
        raw_gap['safety_gap'] = raw_gap['total_supply'] - raw_gap['safety_stock_qty']
        raw_gap['available_supply'] = raw_gap['safety_gap'].clip(lower=0)
        raw_gap['net_gap'] = raw_gap['available_supply'] - raw_gap['total_required_qty']
        
        # Coverage ratio
        raw_gap['coverage_ratio'] = np.where(
            raw_gap['total_required_qty'] > 0,
            raw_gap['available_supply'] / raw_gap['total_required_qty'],
            np.where(raw_gap['total_supply'] > 0, 999, 0)
        )
        
        # Classify status
        raw_gap['gap_status'] = raw_gap.apply(self._classify_gap_status, axis=1)
        raw_gap['priority'] = raw_gap['gap_status'].apply(lambda x: STATUS_CONFIG.get(x, {}).get('priority', 99))
        
        # Sort
        raw_gap = raw_gap.sort_values(['priority', 'net_gap']).reset_index(drop=True)
        
        # Metrics
        metrics = {
            'total_materials': len(raw_gap),
            'shortage_count': len(raw_gap[raw_gap['net_gap'] < 0]),
            'sufficient_count': len(raw_gap[raw_gap['net_gap'] >= 0])
        }
        
        # Alternative analysis
        alt_analysis = pd.DataFrame()
        if include_alternatives and 'is_primary' in raw_gap.columns:
            alt_analysis = self._analyze_alternatives(raw_gap)
            metrics['alternative_available'] = len(alt_analysis[alt_analysis.get('can_cover_shortage', False) == True]) if not alt_analysis.empty else 0
        
        return raw_gap, metrics, alt_analysis
    
    def _analyze_alternatives(self, raw_gap_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze alternative materials for shortage primaries"""
        
        if raw_gap_df.empty or 'is_primary' not in raw_gap_df.columns:
            return pd.DataFrame()
        
        # Get primary materials with shortage
        primary_shortage = raw_gap_df[
            (raw_gap_df['is_primary'] == True) & 
            (raw_gap_df['net_gap'] < 0)
        ]
        
        if primary_shortage.empty:
            return pd.DataFrame()
        
        # Get alternative materials
        alternatives = raw_gap_df[raw_gap_df['is_primary'] == False].copy()
        
        if alternatives.empty:
            return pd.DataFrame()
        
        # Match alternatives to primaries by primary_material_id
        # (alternative materials have primary_material_id pointing to their primary)
        if 'primary_material_id' not in alternatives.columns:
            return pd.DataFrame()
        
        results = []
        for _, primary in primary_shortage.iterrows():
            primary_id = primary.get('material_id')
            if pd.isna(primary_id):
                continue
            
            # Find alternatives that reference this primary
            group_alts = alternatives[alternatives['primary_material_id'] == primary_id]
            for _, alt in group_alts.iterrows():
                can_cover = alt.get('net_gap', 0) >= abs(primary.get('net_gap', 0))
                results.append({
                    'primary_material_id': primary_id,
                    'primary_pt_code': primary.get('material_pt_code'),
                    'primary_net_gap': primary.get('net_gap'),
                    'alternative_material_id': alt['material_id'],
                    'material_pt_code': alt.get('material_pt_code'),
                    'material_name': alt.get('material_name'),
                    'net_gap': alt.get('net_gap'),
                    'alternative_priority': alt.get('alternative_priority', 99),
                    'can_cover_shortage': can_cover
                })
        
        return pd.DataFrame(results) if results else pd.DataFrame()
    
    # =========================================================================
    # ACTION RECOMMENDATIONS
    # =========================================================================
    
    def _generate_actions(
        self,
        result: SupplyChainGAPResult
    ) -> Tuple[List[ActionRecommendation], List[ActionRecommendation], List[ActionRecommendation]]:
        """Generate action recommendations"""
        
        mo_suggestions = []
        po_fg_suggestions = []
        po_raw_suggestions = []
        
        # MO suggestions for manufacturing products
        mfg_shortage = result.get_manufacturing_shortage()
        for _, row in mfg_shortage.iterrows():
            product_id = row['product_id']
            status = result.get_production_status(product_id)
            
            if status.get('can_produce', False):
                action_type = 'USE_ALTERNATIVE' if status.get('status') == 'USE_ALTERNATIVE' else 'CREATE_MO'
                reason = status.get('reason', 'Raw materials available')
            else:
                action_type = 'WAIT_RAW'
                reason = status.get('reason', 'Raw materials insufficient')
            
            mo_suggestions.append(ActionRecommendation(
                action_type=action_type,
                product_id=product_id,
                pt_code=row.get('pt_code', ''),
                product_name=row.get('product_name', ''),
                quantity=abs(row.get('net_gap', 0)),
                uom=row.get('standard_uom', ''),
                priority=row.get('priority', 99),
                reason=reason,
                related_materials=status.get('limiting_materials', [])
            ))
        
        # PO-FG suggestions for trading products
        trading_shortage = result.get_trading_shortage()
        for _, row in trading_shortage.iterrows():
            po_fg_suggestions.append(ActionRecommendation(
                action_type='CREATE_PO_FG',
                product_id=row['product_id'],
                pt_code=row.get('pt_code', ''),
                product_name=row.get('product_name', ''),
                quantity=abs(row.get('net_gap', 0)),
                uom=row.get('standard_uom', ''),
                priority=row.get('priority', 99),
                reason='Trading product - no BOM'
            ))
        
        # PO-Raw suggestions for raw material shortage
        raw_shortage = result.get_raw_shortage()
        for _, row in raw_shortage.iterrows():
            # Check if alternative can cover
            has_alternative = False
            if not result.alternative_analysis_df.empty:
                mat_id = row.get('material_id')
                alts = result.alternative_analysis_df[
                    result.alternative_analysis_df.get('primary_material_id') == mat_id
                ]
                has_alternative = not alts.empty and alts.get('can_cover_shortage', False).any()
            
            if not has_alternative and row.get('is_primary', True):
                po_raw_suggestions.append(ActionRecommendation(
                    action_type='CREATE_PO_RAW',
                    product_id=row.get('material_id', 0),
                    pt_code=row.get('material_pt_code', ''),
                    product_name=row.get('material_name', ''),
                    quantity=abs(row.get('net_gap', 0)),
                    uom=row.get('material_uom', ''),
                    priority=row.get('priority', 99),
                    reason='Raw material shortage'
                ))
        
        return mo_suggestions, po_fg_suggestions, po_raw_suggestions


# Singleton
_calculator_instance = None

def get_calculator() -> SupplyChainGAPCalculator:
    """Get singleton calculator instance"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = SupplyChainGAPCalculator()
    return _calculator_instance