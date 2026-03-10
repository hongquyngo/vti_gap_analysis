# utils/supply_chain_gap/filters.py

"""
Filter UI for Supply Chain GAP Analysis
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
import logging

from .constants import SUPPLY_SOURCES, DEMAND_SOURCES
from .data_loader import SupplyChainDataLoader

logger = logging.getLogger(__name__)


class SupplyChainFilters:
    """Filter UI component for Supply Chain GAP Analysis"""
    
    def __init__(self, data_loader: SupplyChainDataLoader):
        self.data_loader = data_loader
    
    def render_filters(self) -> Dict[str, Any]:
        """
        Render filter UI and return filter values.
        
        Returns:
            Dict with all filter values
        """
        
        # Main filter row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            entity = self._render_entity_filter()
        
        with col2:
            brands = self._render_brand_filter(entity)
        
        with col3:
            products = self._render_product_filter(entity, brands)
        
        # Source filters
        st.markdown("##### Supply & Demand Sources")
        col1, col2 = st.columns(2)
        
        with col1:
            supply_sources = self._render_supply_source_filter()
        
        with col2:
            demand_sources = self._render_demand_source_filter()
        
        # Options - use columns instead of expander
        st.markdown("##### Options")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            include_fg_safety = st.checkbox(
                "FG Safety Stock",
                value=True,
                key="scg_fg_safety",
                help="Consider FG safety stock in available supply"
            )
        
        with col2:
            include_raw_safety = st.checkbox(
                "Raw Safety Stock",
                value=True,
                key="scg_raw_safety",
                help="Consider raw material safety stock"
            )
        
        with col3:
            exclude_expired = st.checkbox(
                "Exclude Expired",
                value=True,
                key="scg_exclude_expired",
                help="Exclude expired inventory from supply"
            )
        
        with col4:
            include_alternatives = st.checkbox(
                "Alternatives",
                value=True,
                key="scg_alternatives",
                help="Analyze alternative materials for BOM"
            )
        
        with col5:
            include_existing_mo = st.checkbox(
                "Existing MO Demand",
                value=True,
                key="scg_existing_mo",
                help="Include raw material demand from existing manufacturing orders"
            )
        
        # Detect MO Expected in supply sources
        include_mo_expected = 'MO_EXPECTED' in supply_sources
        
        # Double-count warning: MO_EXPECTED off + Existing MO on = risk
        if not include_mo_expected and include_existing_mo:
            st.warning(
                "⚠️ **Double-count risk:** MO Expected Output is excluded from FG supply, "
                "but Existing MO Demand is ON at raw material level. "
                "This means FG shortage is not reduced by in-flight MOs, so BOM explosion "
                "generates raw demand that overlaps with the existing MO demand. "
                "**Recommendation:** Enable MO Expected in Supply Sources, or disable Existing MO Demand.",
                icon="⚠️"
            )
        
        return {
            'entity': entity,
            'brands': brands,
            'brands_tuple': tuple(brands) if brands else None,
            'products': products,
            'products_tuple': tuple(products) if products else None,
            'supply_sources': supply_sources,
            'demand_sources': demand_sources,
            'include_fg_safety': include_fg_safety,
            'include_raw_safety': include_raw_safety,
            'exclude_expired': exclude_expired,
            'include_alternatives': include_alternatives,
            'include_existing_mo': include_existing_mo,
            'include_mo_expected': include_mo_expected
        }
    
    def _render_entity_filter(self) -> Optional[str]:
        """Render entity filter"""
        try:
            entities = self.data_loader.get_entities()
        except Exception as e:
            logger.warning(f"Could not load entities: {e}")
            entities = []
        
        options = ['All'] + entities
        selected = st.selectbox(
            "Entity",
            options=options,
            key="scg_entity",
            help="Filter by company/entity"
        )
        
        return None if selected == 'All' else selected
    
    def _render_brand_filter(self, entity: Optional[str]) -> List[str]:
        """Render brand filter"""
        try:
            brands = self.data_loader.get_brands(entity_name=entity)
        except Exception as e:
            logger.warning(f"Could not load brands: {e}")
            brands = []
        
        selected = st.multiselect(
            "Brands",
            options=brands,
            key="scg_brands",
            help="Filter by product brands"
        )
        
        return selected
    
    def _render_product_filter(
        self,
        entity: Optional[str],
        brands: List[str]
    ) -> List[int]:
        """Render product filter"""
        try:
            products_df = self.data_loader.get_products(
                entity_name=entity,
                brand=brands[0] if len(brands) == 1 else None
            )
            product_options = {
                f"{row['pt_code']} - {row['product_name'][:30]}": row['product_id']
                for _, row in products_df.iterrows()
            }
        except Exception as e:
            logger.warning(f"Could not load products: {e}")
            product_options = {}
        
        selected = st.multiselect(
            "Products",
            options=list(product_options.keys()),
            key="scg_products",
            help="Filter by specific products"
        )
        
        return [product_options[p] for p in selected]
    
    def _render_supply_source_filter(self) -> List[str]:
        """Render supply source filter"""
        options = list(SUPPLY_SOURCES.keys())
        
        selected = st.multiselect(
            "Supply Sources",
            options=options,
            default=options,
            format_func=lambda x: SUPPLY_SOURCES[x]['label'],
            key="scg_supply_sources",
            help="Select supply sources to include"
        )
        
        return selected
    
    def _render_demand_source_filter(self) -> List[str]:
        """Render demand source filter"""
        options = list(DEMAND_SOURCES.keys())
        
        selected = st.multiselect(
            "Demand Sources",
            options=options,
            default=options,
            format_func=lambda x: DEMAND_SOURCES[x]['label'],
            key="scg_demand_sources",
            help="Select demand sources to include"
        )
        
        return selected


def get_filters(data_loader: SupplyChainDataLoader) -> SupplyChainFilters:
    """Get filters instance"""
    return SupplyChainFilters(data_loader)