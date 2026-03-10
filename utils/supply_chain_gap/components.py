# utils/supply_chain_gap/components.py

"""
UI Components for Supply Chain GAP Analysis
KPI Cards, Sortable Tables, Drill-Down, Status Summary, Data Freshness

VERSION: 2.0.0
CHANGELOG:
- Sortable columns: Use column_config instead of string pre-formatting
- Drill-down: Click product → see BOM, raw materials, production status
- Data freshness: Show age, staleness warning, refresh button
- Pagination for all tables (Manufacturing, Trading, Raw, Actions)
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging

from .constants import (
    STATUS_CONFIG, GAP_CATEGORIES, PRODUCT_TYPES,
    ACTION_TYPES, RAW_MATERIAL_STATUS, UI_CONFIG,
    SUPPLY_SOURCES, DEMAND_SOURCES
)
from .result import SupplyChainGAPResult

logger = logging.getLogger(__name__)


# =============================================================================
# DATA FRESHNESS INDICATOR
# =============================================================================

def render_data_freshness(state, on_refresh=None):
    """
    Render data freshness indicator with age + staleness warning + refresh.
    
    Args:
        state: SupplyChainStateManager instance
        on_refresh: callback key for refresh button
    
    Returns:
        True if refresh button was clicked
    """
    if not state.has_result():
        return False
    
    age_display = state.get_data_age_display()
    is_stale = state.is_data_stale(threshold_minutes=30)
    last_calc = state.get_last_calculated()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        time_str = last_calc.strftime('%H:%M:%S') if last_calc else ''
        if is_stale:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:6px;">'
                f'<span style="color:#F59E0B;font-size:18px;">⚠️</span>'
                f'<span style="color:#92400E;font-size:13px;">'
                f'Data may be outdated — last analyzed <b>{age_display}</b> ({time_str})'
                f'</span></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:6px;">'
                f'<span style="color:#10B981;font-size:14px;">●</span>'
                f'<span style="color:#6B7280;font-size:13px;">'
                f'Analyzed {age_display} ({time_str})'
                f'</span></div>',
                unsafe_allow_html=True
            )
    
    with col3:
        refresh_clicked = st.button(
            "🔄 Refresh",
            key="scg_refresh_btn",
            use_container_width=True,
            type="secondary"
        )
        if refresh_clicked:
            return True
    
    return False


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
            total = metrics.get('mo_count', 0) + metrics.get('po_fg_count', 0) + metrics.get('po_raw_count', 0)
            _kpi_card("Total Actions", total, icon="📋", color="#6B7280")
        
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
# SORTABLE DATA TABLES
# =============================================================================

def _get_column_config_fg() -> Dict[str, Any]:
    """Column config for FG GAP table — keeps numeric types for sorting"""
    return {
        'pt_code': st.column_config.TextColumn('Code', width='small'),
        'product_name': st.column_config.TextColumn('Product', width='medium'),
        'brand': st.column_config.TextColumn('Brand', width='small'),
        'standard_uom': st.column_config.TextColumn('UOM', width='small'),
        'total_supply': st.column_config.NumberColumn('Supply', format='%,.0f'),
        'total_demand': st.column_config.NumberColumn('Demand', format='%,.0f'),
        'net_gap': st.column_config.NumberColumn('GAP', format='%,.0f'),
        'coverage_pct': st.column_config.ProgressColumn(
            'Coverage',
            format='%.0f%%',
            min_value=0,
            max_value=200
        ),
        'gap_status_display': st.column_config.TextColumn('Status', width='medium'),
        'at_risk_value': st.column_config.NumberColumn('At Risk ($)', format='$%,.0f'),
        'customer_count': st.column_config.NumberColumn('Customers', format='%d'),
    }


def render_fg_table(
    df: pd.DataFrame,
    items_per_page: int = 25,
    current_page: int = 1
) -> Dict[str, Any]:
    """
    Render FG GAP table with sortable columns.
    Numeric columns stay numeric for native Streamlit sorting.
    """
    
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
    
    # Prepare display columns — keep numeric types
    display_cols = [
        'pt_code', 'product_name', 'brand', 'standard_uom',
        'total_supply', 'total_demand', 'net_gap',
        'coverage_pct', 'gap_status_display', 'at_risk_value'
    ]
    
    # Add coverage_pct (percentage for ProgressColumn)
    if 'coverage_ratio' in page_df.columns:
        page_df['coverage_pct'] = (
            pd.to_numeric(page_df['coverage_ratio'], errors='coerce').fillna(0) * 100
        ).clip(0, 200)
    else:
        page_df['coverage_pct'] = 0
    
    # Add formatted status (icon + label) — text column for display
    if 'gap_status' in page_df.columns:
        page_df['gap_status_display'] = page_df['gap_status'].apply(
            lambda x: f"{STATUS_CONFIG.get(x, {}).get('icon', '')} {x.replace('_', ' ').title()}"
        )
    else:
        page_df['gap_status_display'] = ''
    
    # Ensure numeric columns
    for col in ['total_supply', 'total_demand', 'net_gap', 'at_risk_value']:
        if col in page_df.columns:
            page_df[col] = pd.to_numeric(page_df[col], errors='coerce').fillna(0)
    
    available_cols = [c for c in display_cols if c in page_df.columns]
    
    st.dataframe(
        page_df[available_cols],
        column_config=_get_column_config_fg(),
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(page_df) + 38)
    )
    
    return {
        'page': current_page,
        'total_pages': total_pages,
        'total_items': total_items,
        'showing': f"{start_idx + 1}-{end_idx} of {total_items}"
    }


def render_manufacturing_table(
    result: SupplyChainGAPResult,
    items_per_page: int = 25,
    current_page: int = 1
) -> Dict[str, Any]:
    """Render manufacturing products with sortable columns + pagination"""
    
    mfg_shortage = result.get_manufacturing_shortage()
    
    if mfg_shortage.empty:
        st.info("🏭 No manufacturing products with shortage")
        return {}
    
    st.markdown(f"**{len(mfg_shortage)} Manufacturing Products with Shortage**")
    
    # Pagination
    total_items = len(mfg_shortage)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    current_page = min(max(1, current_page), total_pages)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_df = mfg_shortage.iloc[start_idx:end_idx]
    
    # Build display data with numeric types preserved
    display_data = []
    for _, row in page_df.iterrows():
        product_id = row['product_id']
        status = result.get_production_status(product_id)
        
        can_produce = status.get('can_produce', False)
        
        display_data.append({
            'pt_code': row.get('pt_code', ''),
            'product_name': str(row.get('product_name', ''))[:40],
            'net_gap': float(row.get('net_gap', 0)),
            'can_produce': '✅ Yes' if can_produce else '❌ No',
            'production_status': status.get('status', 'UNKNOWN'),
            'reason': status.get('reason', '')[:50],
            'bom_code': status.get('bom_code', '') or ''
        })
    
    display_df = pd.DataFrame(display_data)
    
    st.dataframe(
        display_df,
        column_config={
            'pt_code': st.column_config.TextColumn('Code', width='small'),
            'product_name': st.column_config.TextColumn('Product', width='medium'),
            'net_gap': st.column_config.NumberColumn('GAP', format='%,.0f'),
            'can_produce': st.column_config.TextColumn('Can Produce', width='small'),
            'production_status': st.column_config.TextColumn('Status', width='small'),
            'reason': st.column_config.TextColumn('Reason', width='medium'),
            'bom_code': st.column_config.TextColumn('BOM', width='small'),
        },
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(display_df) + 38)
    )
    
    return {
        'page': current_page,
        'total_pages': total_pages,
        'total_items': total_items,
        'showing': f"{start_idx + 1}-{end_idx} of {total_items}"
    }


def render_trading_table(
    result: SupplyChainGAPResult,
    items_per_page: int = 25,
    current_page: int = 1
) -> Dict[str, Any]:
    """Render trading products with sortable columns + pagination"""
    
    trading_shortage = result.get_trading_shortage()
    
    if trading_shortage.empty:
        st.info("🛒 No trading products with shortage")
        return {}
    
    st.markdown(f"**{len(trading_shortage)} Trading Products with Shortage**")
    
    # Pagination
    total_items = len(trading_shortage)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    current_page = min(max(1, current_page), total_pages)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_df = trading_shortage.iloc[start_idx:end_idx].copy()
    
    # Keep numeric, add display columns
    page_df['at_risk_value'] = pd.to_numeric(page_df.get('at_risk_value', 0), errors='coerce').fillna(0)
    page_df['net_gap'] = pd.to_numeric(page_df.get('net_gap', 0), errors='coerce').fillna(0)
    page_df['action'] = '🛒 Create PO'
    
    display_cols = ['pt_code', 'product_name', 'brand', 'net_gap', 'at_risk_value', 'action']
    available = [c for c in display_cols if c in page_df.columns]
    
    st.dataframe(
        page_df[available],
        column_config={
            'pt_code': st.column_config.TextColumn('Code', width='small'),
            'product_name': st.column_config.TextColumn('Product', width='medium'),
            'brand': st.column_config.TextColumn('Brand', width='small'),
            'net_gap': st.column_config.NumberColumn('GAP', format='%,.0f'),
            'at_risk_value': st.column_config.NumberColumn('At Risk ($)', format='$%,.0f'),
            'action': st.column_config.TextColumn('Action', width='small'),
        },
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(page_df) + 38)
    )
    
    return {
        'page': current_page,
        'total_pages': total_pages,
        'total_items': total_items,
        'showing': f"{start_idx + 1}-{end_idx} of {total_items}"
    }


def render_raw_material_table(
    result: SupplyChainGAPResult,
    items_per_page: int = 25,
    current_page: int = 1
) -> Dict[str, Any]:
    """Render raw material GAP table with sortable columns + pagination"""
    
    raw_df = result.raw_gap_df.copy()
    
    if raw_df.empty:
        st.info("🧪 No raw material data")
        return {}
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_primary_only = st.checkbox("Primary only", value=False, key="raw_primary_only")
    with col2:
        show_shortage_only = st.checkbox("Shortage only", value=False, key="raw_shortage_only")
    
    if show_primary_only and 'is_primary' in raw_df.columns:
        raw_df = raw_df[raw_df['is_primary'].isin([1, True])]
    
    if show_shortage_only and 'net_gap' in raw_df.columns:
        raw_df = raw_df[raw_df['net_gap'] < 0]
    
    st.markdown(f"**{len(raw_df)} Raw Materials**")
    
    if raw_df.empty:
        st.info("No materials match current filters")
        return {}
    
    # Pagination
    total_items = len(raw_df)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    current_page = min(max(1, current_page), total_pages)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_df = raw_df.iloc[start_idx:end_idx].copy()
    
    # Ensure numeric types
    for col in ['total_required_qty', 'total_supply', 'net_gap', 'safety_stock_qty']:
        if col in page_df.columns:
            page_df[col] = pd.to_numeric(page_df[col], errors='coerce').fillna(0)
    
    # Coverage percentage
    if 'coverage_ratio' in page_df.columns:
        page_df['coverage_pct'] = (
            pd.to_numeric(page_df['coverage_ratio'], errors='coerce').fillna(0) * 100
        ).clip(0, 200)
    else:
        page_df['coverage_pct'] = 0
    
    display_cols = [
        'material_pt_code', 'material_name', 'material_type',
        'total_required_qty', 'total_supply', 'net_gap', 'coverage_pct'
    ]
    available = [c for c in display_cols if c in page_df.columns]
    
    st.dataframe(
        page_df[available],
        column_config={
            'material_pt_code': st.column_config.TextColumn('Code', width='small'),
            'material_name': st.column_config.TextColumn('Material', width='medium'),
            'material_type': st.column_config.TextColumn('Type', width='small'),
            'total_required_qty': st.column_config.NumberColumn('Required', format='%,.0f'),
            'total_supply': st.column_config.NumberColumn('Supply', format='%,.0f'),
            'net_gap': st.column_config.NumberColumn('GAP', format='%,.0f'),
            'coverage_pct': st.column_config.ProgressColumn(
                'Coverage', format='%.0f%%', min_value=0, max_value=200
            ),
        },
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(page_df) + 38)
    )
    
    return {
        'page': current_page,
        'total_pages': total_pages,
        'total_items': total_items,
        'showing': f"{start_idx + 1}-{end_idx} of {total_items}"
    }


def render_action_table(
    result: SupplyChainGAPResult,
    action_type: str = 'all',
    items_per_page: int = 50,
    current_page: int = 1
) -> Dict[str, Any]:
    """Render action recommendations with sortable columns + pagination"""
    
    actions = result.get_all_actions()
    
    if not actions:
        st.info("📋 No actions to display")
        return {}
    
    # Filter by type
    if action_type == 'mo':
        actions = [a for a in actions if a['action_type'] in ['CREATE_MO', 'WAIT_RAW', 'USE_ALTERNATIVE']]
    elif action_type == 'po_fg':
        actions = [a for a in actions if a['action_type'] == 'CREATE_PO_FG']
    elif action_type == 'po_raw':
        actions = [a for a in actions if a['action_type'] == 'CREATE_PO_RAW']
    
    if not actions:
        st.info("No actions of this type")
        return {}
    
    st.markdown(f"**{len(actions)} Actions**")
    
    # Build dataframe with numeric types preserved
    rows = []
    for action in actions:
        action_config = ACTION_TYPES.get(action['action_type'], {})
        icon = action_config.get('icon', '📝')
        label = action_config.get('label', action['action_type'])
        
        rows.append({
            'action_display': f"{icon} {label}",
            'pt_code': action.get('pt_code', ''),
            'product_name': str(action.get('product_name', ''))[:40],
            'quantity': float(action.get('quantity', 0)),
            'uom': action.get('uom', ''),
            'priority': int(action.get('priority', 99)),
            'reason': str(action.get('reason', ''))[:50]
        })
    
    all_df = pd.DataFrame(rows)
    
    # Pagination
    total_items = len(all_df)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    current_page = min(max(1, current_page), total_pages)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_df = all_df.iloc[start_idx:end_idx]
    
    st.dataframe(
        page_df,
        column_config={
            'action_display': st.column_config.TextColumn('Action', width='medium'),
            'pt_code': st.column_config.TextColumn('Code', width='small'),
            'product_name': st.column_config.TextColumn('Name', width='medium'),
            'quantity': st.column_config.NumberColumn('Qty', format='%,.0f'),
            'uom': st.column_config.TextColumn('UOM', width='small'),
            'priority': st.column_config.NumberColumn('Priority', format='%d'),
            'reason': st.column_config.TextColumn('Reason', width='medium'),
        },
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(page_df) + 38)
    )
    
    return {
        'page': current_page,
        'total_pages': total_pages,
        'total_items': total_items,
        'showing': f"{start_idx + 1}-{end_idx} of {total_items}"
    }


# =============================================================================
# DRILL-DOWN: FG PRODUCT → RAW MATERIALS
# =============================================================================

def render_product_drilldown(result: SupplyChainGAPResult, filtered_df: pd.DataFrame):
    """
    Render drill-down panel: select a FG product → see full detail.
    
    Shows:
    - Supply/Demand breakdown
    - Product classification (MFG/Trading)
    - BOM detail + Raw material status (if Manufacturing)
    - Recommended action
    """
    
    if filtered_df.empty or 'product_id' not in filtered_df.columns:
        return
    
    st.divider()
    st.markdown("#### 🔍 Product Drill-Down")
    
    # Build product options
    options = {}
    for _, row in filtered_df.iterrows():
        pid = row['product_id']
        code = row.get('pt_code', '')
        name = str(row.get('product_name', ''))[:40]
        gap = row.get('net_gap', 0)
        icon = '🔴' if gap < 0 else '🟢' if gap > 0 else '⚪'
        options[f"{icon} {code} — {name} (GAP: {gap:,.0f})"] = pid
    
    # Selection
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_label = st.selectbox(
            "Select product to inspect",
            options=['— Select a product —'] + list(options.keys()),
            key="scg_drilldown_select",
            label_visibility="collapsed",
            placeholder="🔍 Select a product to inspect..."
        )
    with col2:
        if st.button("✖ Clear", key="scg_drilldown_clear", use_container_width=True):
            st.session_state['scg_drilldown_select'] = '— Select a product —'
            st.rerun()
    
    if selected_label == '— Select a product —' or selected_label not in options:
        st.caption("💡 Select a product above to see supply/demand breakdown, BOM details, and raw material status.")
        return
    
    product_id = options[selected_label]
    
    # Get product row
    product_row = filtered_df[filtered_df['product_id'] == product_id]
    if product_row.empty:
        return
    product = product_row.iloc[0]
    
    # -------------------------------------------------------------------------
    # Section 1: Product Summary Card
    # -------------------------------------------------------------------------
    gap_val = float(product.get('net_gap', 0))
    status = product.get('gap_status', 'UNKNOWN')
    status_cfg = STATUS_CONFIG.get(status, {})
    status_icon = status_cfg.get('icon', '❓')
    status_color = status_cfg.get('color', '#6B7280')
    
    st.markdown(f"""
    <div style="background:white;border-radius:10px;padding:16px 20px;border:1px solid #E5E7EB;
                box-shadow:0 1px 3px rgba(0,0,0,0.08);margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:11px;color:#6B7280;text-transform:uppercase;letter-spacing:0.5px;">
                    {product.get('pt_code', '')} · {product.get('brand', '')} · {product.get('standard_uom', '')}
                </div>
                <div style="font-size:18px;font-weight:700;color:#1F2937;margin-top:4px;">
                    {product.get('product_name', '')}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:28px;font-weight:800;color:{status_color};">{gap_val:,.0f}</div>
                <div style="font-size:12px;color:{status_color};">{status_icon} {status.replace('_', ' ').title()}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # Section 2: Supply / Demand / Safety Breakdown
    # -------------------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📦 Supply Breakdown**")
        supply_items = []
        for src_key in ['supply_inventory', 'supply_can_pending', 'supply_warehouse_transfer', 'supply_purchase_order']:
            val = product.get(src_key, None)
            if pd.notna(val) and val > 0:
                # Map column name back to source label
                source_map = {
                    'supply_inventory': 'INVENTORY',
                    'supply_can_pending': 'CAN_PENDING',
                    'supply_warehouse_transfer': 'WAREHOUSE_TRANSFER',
                    'supply_purchase_order': 'PURCHASE_ORDER'
                }
                src_label = SUPPLY_SOURCES.get(source_map.get(src_key, ''), {}).get('label', src_key)
                supply_items.append(f"- {src_label}: **{val:,.0f}**")
        
        total_supply = product.get('total_supply', 0)
        if supply_items:
            st.markdown('\n'.join(supply_items))
        st.markdown(f"**Total Supply: {total_supply:,.0f}**")
    
    with col2:
        st.markdown("**📊 Demand Breakdown**")
        demand_items = []
        for src_key in ['demand_oc_pending', 'demand_forecast']:
            val = product.get(src_key, None)
            if pd.notna(val) and val > 0:
                source_map = {
                    'demand_oc_pending': 'OC_PENDING',
                    'demand_forecast': 'FORECAST'
                }
                src_label = DEMAND_SOURCES.get(source_map.get(src_key, ''), {}).get('label', src_key)
                demand_items.append(f"- {src_label}: **{val:,.0f}**")
        
        total_demand = product.get('total_demand', 0)
        if demand_items:
            st.markdown('\n'.join(demand_items))
        st.markdown(f"**Total Demand: {total_demand:,.0f}**")
    
    with col3:
        st.markdown("**📐 GAP Calculation**")
        safety = product.get('safety_stock_qty', 0)
        available = product.get('available_supply', 0)
        coverage = product.get('coverage_ratio', 0)
        at_risk = product.get('at_risk_value', 0)
        
        st.markdown(f"- Safety Stock: **{safety:,.0f}**")
        st.markdown(f"- Available Supply: **{available:,.0f}**")
        st.markdown(f"- Net GAP: **{gap_val:,.0f}**")
        if pd.notna(coverage) and coverage < 100:
            st.markdown(f"- Coverage: **{coverage*100:.1f}%**")
        else:
            st.markdown("- Coverage: **N/A**")
        if at_risk > 0:
            st.markdown(f"- 💰 At Risk: **${at_risk:,.0f}**")
    
    # -------------------------------------------------------------------------
    # Section 3: Classification + Production Status
    # -------------------------------------------------------------------------
    prod_status = result.get_production_status(product_id)
    prod_type = prod_status.get('product_type', 'UNKNOWN')
    
    st.divider()
    
    if prod_type == 'MANUFACTURING':
        _render_drilldown_manufacturing(result, product_id, product, prod_status)
    elif prod_type == 'TRADING':
        _render_drilldown_trading(product, prod_status)
    else:
        st.info("ℹ️ Product classification not available. Check if BOM data is loaded.")


def _render_drilldown_manufacturing(
    result: SupplyChainGAPResult,
    product_id: int,
    product: pd.Series,
    prod_status: Dict[str, Any]
):
    """Render drill-down detail for manufacturing product"""
    
    can_produce = prod_status.get('can_produce', False)
    bom_code = prod_status.get('bom_code', '') or 'N/A'
    reason = prod_status.get('reason', '')
    limiting = prod_status.get('limiting_materials', [])
    
    # Status header
    if can_produce:
        if prod_status.get('status') == 'USE_ALTERNATIVE':
            st.success(f"🏭 **Manufacturing** — BOM: `{bom_code}` — 🔄 Can produce using alternative materials")
        else:
            st.success(f"🏭 **Manufacturing** — BOM: `{bom_code}` — ✅ Can produce (all materials available)")
    else:
        st.warning(f"🏭 **Manufacturing** — BOM: `{bom_code}` — ❌ Cannot produce: {reason}")
        if limiting:
            st.caption(f"⚠️ Limiting materials: `{'`, `'.join(limiting[:5])}`")
    
    # Raw materials table
    materials = result.get_raw_materials_for_fg(product_id)
    
    if materials.empty:
        st.info("No BOM materials found for this product")
        return
    
    st.markdown(f"**🧪 Raw Materials ({len(materials)} items)**")
    
    # Build display with numeric types
    mat_data = []
    for _, mat in materials.iterrows():
        mat_gap = mat.get('net_gap', None)
        is_primary = mat.get('is_primary', 1) in [1, True]
        
        mat_data.append({
            'material_pt_code': mat.get('material_pt_code', ''),
            'material_name': str(mat.get('material_name', ''))[:35],
            'type_label': '🔵 Primary' if is_primary else '🔄 Alt',
            'quantity_per_output': float(mat.get('quantity_per_output', 0) or 0),
            'scrap_rate': float(mat.get('scrap_rate', 0) or 0),
            'total_supply': float(mat.get('total_supply', 0)) if pd.notna(mat.get('total_supply')) else 0,
            'net_gap': float(mat_gap) if pd.notna(mat_gap) else None,
            'status_icon': '✅' if (pd.notna(mat_gap) and mat_gap >= 0) else ('🔴' if pd.notna(mat_gap) else '❓')
        })
    
    mat_df = pd.DataFrame(mat_data)
    
    st.dataframe(
        mat_df,
        column_config={
            'material_pt_code': st.column_config.TextColumn('Code', width='small'),
            'material_name': st.column_config.TextColumn('Material', width='medium'),
            'type_label': st.column_config.TextColumn('Type', width='small'),
            'quantity_per_output': st.column_config.NumberColumn('Qty/Output', format='%.2f'),
            'scrap_rate': st.column_config.NumberColumn('Scrap %', format='%.1f%%'),
            'total_supply': st.column_config.NumberColumn('Supply', format='%,.0f'),
            'net_gap': st.column_config.NumberColumn('GAP', format='%,.0f'),
            'status_icon': st.column_config.TextColumn('', width='small'),
        },
        use_container_width=True,
        hide_index=True,
        height=min(300, 35 * len(mat_df) + 38)
    )
    
    # Action recommendation
    gap_val = float(product.get('net_gap', 0))
    if gap_val < 0:
        st.markdown("**📋 Recommended Action:**")
        uom = product.get('standard_uom', '')
        qty = abs(gap_val)
        if can_produce:
            if prod_status.get('status') == 'USE_ALTERNATIVE':
                st.markdown(f"🔄 **USE_ALTERNATIVE** — Produce `{qty:,.0f}` {uom} using alternative materials")
            else:
                st.markdown(f"🏭 **CREATE_MO** — Produce `{qty:,.0f}` {uom} (all materials sufficient)")
        else:
            st.markdown(f"⏳ **WAIT_RAW** — Need raw materials before producing `{qty:,.0f}` {uom}")
            if limiting:
                st.markdown(f"📦 **CREATE_PO_RAW** — Purchase missing raw materials: `{'`, `'.join(limiting[:5])}`")


def _render_drilldown_trading(product: pd.Series, prod_status: Dict[str, Any]):
    """Render drill-down detail for trading product"""
    
    gap_val = float(product.get('net_gap', 0))
    
    st.info("🛒 **Trading** — No BOM (purchase directly from supplier)")
    
    if gap_val < 0:
        st.markdown("**📋 Recommended Action:**")
        st.markdown(f"🛒 **CREATE_PO_FG** — Purchase `{abs(gap_val):,.0f}` {product.get('standard_uom', '')} directly")


# =============================================================================
# PAGINATION
# =============================================================================

def render_pagination(current_page: int, total_pages: int, key_prefix: str = "main") -> int:
    """Render pagination controls with page info"""
    
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
        st.markdown(
            f"<div style='text-align:center;padding:8px;color:#6B7280;font-size:13px;'>"
            f"Page {current_page} of {total_pages}</div>",
            unsafe_allow_html=True
        )
    
    with cols[3]:
        if st.button("▶️", key=f"{key_prefix}_next", disabled=current_page >= total_pages):
            return current_page + 1
    
    with cols[4]:
        if st.button("⏭️", key=f"{key_prefix}_last", disabled=current_page >= total_pages):
            return total_pages
    
    return current_page