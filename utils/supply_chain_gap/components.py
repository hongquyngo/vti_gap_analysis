# utils/supply_chain_gap/components.py

"""
UI Components for Supply Chain GAP Analysis
KPI Cards, Tables, Status Summary, etc.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List
import logging

from .constants import (
    STATUS_CONFIG, GAP_CATEGORIES, PRODUCT_TYPES, 
    ACTION_TYPES, RAW_MATERIAL_STATUS, UI_CONFIG
)
from .result import SupplyChainGAPResult

logger = logging.getLogger(__name__)


# =============================================================================
# KPI CARDS
# =============================================================================

def render_kpi_cards(result: SupplyChainGAPResult):
    """Render KPI cards for all levels"""
    
    metrics = result.get_metrics()
    
    # Row 1: FG Overview
    st.markdown("##### 📊 Finished Goods")
    cols = st.columns(5)
    
    with cols[0]:
        _kpi_card("Total Products", metrics.get('fg_total', 0), icon="📦", color="#6B7280")
    
    with cols[1]:
        _kpi_card("Shortage", metrics.get('fg_shortage', 0), icon="🔴", color="#DC2626")
    
    with cols[2]:
        _kpi_card("Surplus", metrics.get('fg_surplus', 0), icon="📈", color="#3B82F6")
    
    with cols[3]:
        at_risk = metrics.get('at_risk_value', 0)
        _kpi_card("At Risk Value", f"${at_risk:,.0f}", icon="💰", color="#F59E0B")
    
    with cols[4]:
        _kpi_card("Affected Customers", metrics.get('affected_customers', 0), icon="👥", color="#8B5CF6")
    
    # Row 2: Classification
    if result.has_classification():
        st.markdown("##### 🏭 Product Classification")
        cols = st.columns(4)
        
        with cols[0]:
            _kpi_card("Manufacturing", metrics.get('manufacturing_count', 0), icon="🏭", color="#3B82F6")
        
        with cols[1]:
            _kpi_card("Trading", metrics.get('trading_count', 0), icon="🛒", color="#10B981")
        
        with cols[2]:
            _kpi_card("Raw Materials", metrics.get('raw_total', 0), icon="🧪", color="#8B5CF6")
        
        with cols[3]:
            _kpi_card("Raw Shortage", metrics.get('raw_shortage', 0), icon="⚠️", color="#DC2626")
    
    # Row 3: Actions
    if result.has_actions():
        st.markdown("##### 📋 Actions Required")
        cols = st.columns(4)
        
        with cols[0]:
            _kpi_card("Total Actions", metrics.get('mo_count', 0) + metrics.get('po_fg_count', 0) + metrics.get('po_raw_count', 0), icon="📋", color="#6B7280")
        
        with cols[1]:
            _kpi_card("MO to Create", metrics.get('mo_count', 0), icon="🏭", color="#3B82F6")
        
        with cols[2]:
            _kpi_card("PO for FG", metrics.get('po_fg_count', 0), icon="🛒", color="#10B981")
        
        with cols[3]:
            _kpi_card("PO for Raw", metrics.get('po_raw_count', 0), icon="📦", color="#8B5CF6")


def _kpi_card(label: str, value: Any, icon: str = "📊", color: str = "#3B82F6"):
    """Render single KPI card"""
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid {color};
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ">
        <div style="font-size: 20px; margin-bottom: 4px;">{icon}</div>
        <div style="font-size: 24px; font-weight: 700; color: #1F2937;">{value}</div>
        <div style="font-size: 12px; color: #6B7280;">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# STATUS SUMMARY
# =============================================================================

def render_status_summary(gap_df: pd.DataFrame, key_prefix: str = "fg"):
    """Render status distribution summary"""
    
    if gap_df.empty or 'gap_status' not in gap_df.columns:
        return
    
    status_counts = gap_df['gap_status'].value_counts()
    
    cols = st.columns(min(len(status_counts), 6))
    
    for i, (status, count) in enumerate(status_counts.items()):
        if i >= 6:
            break
        config = STATUS_CONFIG.get(status, {})
        icon = config.get('icon', '❓')
        color = config.get('color', '#6B7280')
        
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background: white; border-radius: 8px; border: 1px solid #E5E7EB;">
                <span style="font-size: 18px;">{icon}</span>
                <div style="font-size: 20px; font-weight: 600; color: {color};">{count}</div>
                <div style="font-size: 11px; color: #6B7280;">{status.replace('_', ' ').title()}</div>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# QUICK FILTER
# =============================================================================

def render_quick_filter(key_prefix: str = "fg") -> str:
    """Render quick filter buttons"""
    
    options = {
        'all': '📋 All',
        'shortage': '🔴 Shortage',
        'surplus': '📈 Surplus',
        'critical': '🚨 Critical'
    }
    
    cols = st.columns(len(options))
    
    selected = st.session_state.get(f'{key_prefix}_quick_filter', 'all')
    
    for i, (key, label) in enumerate(options.items()):
        with cols[i]:
            if st.button(
                label,
                key=f"{key_prefix}_qf_{key}",
                use_container_width=True,
                type="primary" if selected == key else "secondary"
            ):
                st.session_state[f'{key_prefix}_quick_filter'] = key
                st.rerun()
    
    return st.session_state.get(f'{key_prefix}_quick_filter', 'all')


def apply_quick_filter(df: pd.DataFrame, filter_type: str) -> pd.DataFrame:
    """Apply quick filter to dataframe"""
    
    if df.empty or 'net_gap' not in df.columns:
        return df
    
    if filter_type == 'shortage':
        return df[df['net_gap'] < 0]
    elif filter_type == 'surplus':
        return df[df['net_gap'] > 0]
    elif filter_type == 'critical':
        return df[df['gap_status'].isin(['CRITICAL_SHORTAGE', 'SEVERE_SHORTAGE'])]
    else:
        return df


# =============================================================================
# DATA TABLES
# =============================================================================

def render_fg_table(
    df: pd.DataFrame,
    items_per_page: int = 25,
    current_page: int = 1
) -> Dict[str, Any]:
    """Render FG GAP table"""
    
    if df.empty:
        st.info("No data to display")
        return {}
    
    # Pagination
    total_items = len(df)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    current_page = min(max(1, current_page), total_pages)
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_df = df.iloc[start_idx:end_idx].copy()
    
    # Select display columns
    display_cols = [
        'pt_code', 'product_name', 'brand', 'standard_uom',
        'total_supply', 'total_demand', 'net_gap', 'coverage_ratio', 'gap_status'
    ]
    available_cols = [c for c in display_cols if c in page_df.columns]
    
    display_df = page_df[available_cols].copy()
    
    # Format columns
    if 'coverage_ratio' in display_df.columns:
        display_df['coverage_ratio'] = display_df['coverage_ratio'].apply(
            lambda x: f"{x*100:.1f}%" if pd.notna(x) and x < 100 else 'N/A'
        )
    
    if 'gap_status' in display_df.columns:
        display_df['gap_status'] = display_df['gap_status'].apply(
            lambda x: f"{STATUS_CONFIG.get(x, {}).get('icon', '')} {x.replace('_', ' ').title()}"
        )
    
    # Rename columns
    display_df.columns = ['Code', 'Product', 'Brand', 'UOM', 'Supply', 'Demand', 'GAP', 'Coverage', 'Status'][:len(available_cols)]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    return {
        'page': current_page,
        'total_pages': total_pages,
        'total_items': total_items,
        'showing': f"{start_idx + 1}-{end_idx} of {total_items}"
    }


def render_manufacturing_table(result: SupplyChainGAPResult, items_per_page: int = 25):
    """Render manufacturing products with production status"""
    
    mfg_shortage = result.get_manufacturing_shortage()
    
    if mfg_shortage.empty:
        st.info("🏭 No manufacturing products with shortage")
        return
    
    st.markdown(f"**{len(mfg_shortage)} Manufacturing Products with Shortage**")
    
    # Build display data
    display_data = []
    for _, row in mfg_shortage.head(items_per_page).iterrows():
        product_id = row['product_id']
        status = result.get_production_status(product_id)
        
        can_produce = status.get('can_produce', False)
        status_icon = '✅' if can_produce else '⚠️'
        reason = status.get('reason', '')[:40]
        
        display_data.append({
            'Code': row.get('pt_code', ''),
            'Product': str(row.get('product_name', ''))[:35],
            'GAP': row.get('net_gap', 0),
            'Can Produce': status_icon,
            'Status': status.get('status', 'UNKNOWN'),
            'Reason': reason
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_trading_table(result: SupplyChainGAPResult, items_per_page: int = 25):
    """Render trading products"""
    
    trading_shortage = result.get_trading_shortage()
    
    if trading_shortage.empty:
        st.info("🛒 No trading products with shortage")
        return
    
    st.markdown(f"**{len(trading_shortage)} Trading Products with Shortage**")
    
    # Select columns
    display_cols = ['pt_code', 'product_name', 'brand', 'net_gap', 'gap_status']
    available_cols = [c for c in display_cols if c in trading_shortage.columns]
    
    display_df = trading_shortage[available_cols].head(items_per_page).copy()
    display_df.columns = ['Code', 'Product', 'Brand', 'GAP', 'Status'][:len(available_cols)]
    display_df['Action'] = '🛒 Create PO'
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_raw_material_table(result: SupplyChainGAPResult, items_per_page: int = 25):
    """Render raw material GAP table"""
    
    raw_df = result.raw_gap_df.copy()
    
    if raw_df.empty:
        st.info("🧪 No raw material data")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_primary_only = st.checkbox("Primary only", value=False, key="raw_primary_only")
    with col2:
        show_shortage_only = st.checkbox("Shortage only", value=False, key="raw_shortage_only")
    
    if show_primary_only and 'is_primary' in raw_df.columns:
        raw_df = raw_df[raw_df['is_primary'] == True]
    
    if show_shortage_only and 'net_gap' in raw_df.columns:
        raw_df = raw_df[raw_df['net_gap'] < 0]
    
    st.markdown(f"**{len(raw_df)} Raw Materials**")
    
    # Build display
    display_data = []
    for _, row in raw_df.head(items_per_page).iterrows():
        gap = row.get('net_gap', None)
        gap_display = f"{gap:,.0f}" if pd.notna(gap) else '-'
        coverage = row.get('coverage_ratio', None)
        coverage_display = f"{coverage*100:.0f}%" if pd.notna(coverage) and coverage < 100 else '-'
        
        display_data.append({
            'Code': row.get('material_pt_code', ''),
            'Material': str(row.get('material_name', ''))[:30],
            'Type': row.get('material_type', ''),
            'Required': f"{row.get('total_required_qty', 0):,.0f}",
            'Supply': f"{row.get('total_supply', 0):,.0f}",
            'GAP': gap_display,
            'Coverage': coverage_display
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_action_table(result: SupplyChainGAPResult, action_type: str = 'all'):
    """Render action recommendations table"""
    
    actions = result.get_all_actions()
    
    if not actions:
        st.info("📋 No actions to display")
        return
    
    # Filter by type
    if action_type == 'mo':
        actions = [a for a in actions if a['action_type'] in ['CREATE_MO', 'WAIT_RAW', 'USE_ALTERNATIVE']]
    elif action_type == 'po_fg':
        actions = [a for a in actions if a['action_type'] == 'CREATE_PO_FG']
    elif action_type == 'po_raw':
        actions = [a for a in actions if a['action_type'] == 'CREATE_PO_RAW']
    
    if not actions:
        st.info("No actions of this type")
        return
    
    st.markdown(f"**{len(actions)} Actions**")
    
    # Build display
    display_data = []
    for action in actions[:50]:  # Limit to 50
        action_config = ACTION_TYPES.get(action['action_type'], {})
        icon = action_config.get('icon', '📝')
        label = action_config.get('label', action['action_type'])
        
        display_data.append({
            'Action': f"{icon} {label}",
            'Code': action.get('pt_code', ''),
            'Name': str(action.get('product_name', ''))[:30],
            'Qty': f"{action.get('quantity', 0):,.0f}",
            'UOM': action.get('uom', ''),
            'Priority': action.get('priority', 99),
            'Reason': str(action.get('reason', ''))[:40]
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


# =============================================================================
# PAGINATION
# =============================================================================

def render_pagination(current_page: int, total_pages: int, key_prefix: str = "main") -> int:
    """Render pagination controls"""
    
    if total_pages <= 1:
        return current_page
    
    cols = st.columns([1, 1, 2, 1, 1])
    
    with cols[0]:
        if st.button("⏮️", key=f"{key_prefix}_first", disabled=current_page <= 1):
            return 1
    
    with cols[1]:
        if st.button("◀️", key=f"{key_prefix}_prev", disabled=current_page <= 1):
            return current_page - 1
    
    with cols[2]:
        st.markdown(f"<div style='text-align: center; padding: 8px;'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)
    
    with cols[3]:
        if st.button("▶️", key=f"{key_prefix}_next", disabled=current_page >= total_pages):
            return current_page + 1
    
    with cols[4]:
        if st.button("⏭️", key=f"{key_prefix}_last", disabled=current_page >= total_pages):
            return total_pages
    
    return current_page
