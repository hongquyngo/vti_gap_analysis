# pages/3_🔬_Supply_Chain_GAP.py

"""
Supply Chain GAP Analysis Page
Full multi-level analysis: FG + Raw Materials
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, Any
import os
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Supply Chain GAP",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import utilities
project_root = os.environ.get('PROJECT_ROOT', Path(__file__).parent.parent)
if str(project_root) not in os.sys.path:
    os.sys.path.insert(0, str(project_root))

from utils.auth import AuthManager
from utils.supply_chain_gap import (
    VERSION,
    get_state,
    get_data_loader,
    get_calculator,
    get_filters,
    get_charts,
    get_formatter,
    export_to_excel,
    get_export_filename,
    render_kpi_cards,
    render_status_summary,
    render_quick_filter,
    apply_quick_filter,
    render_fg_table,
    render_manufacturing_table,
    render_trading_table,
    render_raw_material_table,
    render_action_table,
    render_pagination,
    render_help_dialog,
    UI_CONFIG
)


def initialize_system():
    """Initialize all components"""
    state = get_state()
    data_loader = get_data_loader()
    calculator = get_calculator()
    formatter = get_formatter()
    filters = get_filters(data_loader)
    charts = get_charts()
    
    return state, data_loader, calculator, formatter, filters, charts


def calculate_gap(
    data_loader,
    calculator,
    filter_values: Dict[str, Any]
):
    """Load all data and calculate full Supply Chain GAP"""
    
    with st.spinner("🔬 Calculating Supply Chain GAP..."):
        
        # Load FG Supply
        fg_supply = data_loader.load_fg_supply(
            entity_name=filter_values.get('entity'),
            product_ids=filter_values.get('products_tuple'),
            brands=filter_values.get('brands_tuple'),
            exclude_expired=filter_values.get('exclude_expired', True)
        )
        
        # Load FG Demand
        fg_demand = data_loader.load_fg_demand(
            entity_name=filter_values.get('entity'),
            product_ids=filter_values.get('products_tuple'),
            brands=filter_values.get('brands_tuple')
        )
        
        # Load FG Safety Stock
        fg_safety = None
        if filter_values.get('include_fg_safety', True):
            fg_safety = data_loader.load_fg_safety_stock(
                entity_name=filter_values.get('entity'),
                product_ids=filter_values.get('products_tuple')
            )
        
        # Validate FG data
        if fg_supply.empty and fg_demand.empty:
            st.warning("No FG data available for selected filters")
            return None
        
        # Load Classification
        classification = data_loader.load_product_classification(
            entity_name=filter_values.get('entity'),
            product_ids=filter_values.get('products_tuple')
        )
        
        # Load BOM Explosion
        bom_explosion = data_loader.load_bom_explosion(
            entity_name=filter_values.get('entity'),
            include_alternatives=filter_values.get('include_alternatives', True)
        )
        
        # Load Existing MO Demand
        existing_mo = None
        if filter_values.get('include_existing_mo', True):
            existing_mo = data_loader.load_existing_mo_demand(
                entity_name=filter_values.get('entity')
            )
        
        # Load Raw Material Supply
        raw_supply = data_loader.load_raw_material_supply_summary(
            entity_name=filter_values.get('entity')
        )
        
        # Load Raw Safety Stock
        raw_safety = None
        if filter_values.get('include_raw_safety', True):
            raw_safety = data_loader.load_raw_material_safety_stock(
                entity_name=filter_values.get('entity')
            )
        
        # Calculate full GAP
        result = calculator.calculate(
            fg_supply_df=fg_supply,
            fg_demand_df=fg_demand,
            fg_safety_stock_df=fg_safety,
            classification_df=classification,
            bom_explosion_df=bom_explosion,
            existing_mo_demand_df=existing_mo,
            raw_supply_df=raw_supply,
            raw_safety_stock_df=raw_safety,
            selected_supply_sources=filter_values.get('supply_sources'),
            selected_demand_sources=filter_values.get('demand_sources'),
            include_fg_safety=filter_values.get('include_fg_safety', True),
            include_raw_safety=filter_values.get('include_raw_safety', True),
            include_alternatives=filter_values.get('include_alternatives', True),
            include_existing_mo=filter_values.get('include_existing_mo', True)
        )
        
        logger.info(f"Supply Chain GAP calculated: {result.get_summary()}")
        return result


def main():
    """Main application"""
    
    # Authentication check
    auth_manager = AuthManager()
    if not auth_manager.check_session():
        st.warning("⚠️ Please login to access this page")
        st.stop()
    
    # Initialize
    state, data_loader, calculator, formatter, filters, charts = initialize_system()
    
    # Page header
    st.title("🔬 Supply Chain GAP Analysis")
    st.markdown("Full Multi-Level Analysis: FG + Raw Materials")
    
    # Help dialog - accessible from main area
    render_help_dialog()
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"👤 **User:** {auth_manager.get_user_display_name()}")
        if st.button("🚪 Logout", use_container_width=True):
            auth_manager.logout()
            st.rerun()
        
        st.divider()
        st.caption(f"Version {VERSION}")
    
    # Filters section
    with st.expander("🔧 **Configuration**", expanded=True):
        filter_values = filters.render_filters()
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            state.reset_filters()
            st.rerun()
    
    with col2:
        calculate_clicked = st.button(
            "🔬 Analyze",
            type="primary",
            use_container_width=True
        )
    
    with col3:
        if state.has_result():
            st.success("✅ Results ready")
        else:
            st.info("👆 Click Analyze to start")
    
    # Calculate if needed
    if calculate_clicked:
        try:
            result = calculate_gap(data_loader, calculator, filter_values)
            if result:
                state.set_filters(filter_values)
                state.set_result(result)
                st.rerun()
        except Exception as e:
            logger.error(f"Calculation failed: {e}", exc_info=True)
            st.error(f"❌ Calculation failed: {str(e)}")
            st.stop()
    
    # Display results
    result = state.get_result()
    
    if not result:
        st.info("Configure filters and click 'Analyze' to begin")
        
        # Show feature overview
        with st.expander("ℹ️ About Supply Chain GAP Analysis", expanded=True):
            st.markdown("""
            ### Full Multi-Level Analysis
            
            **Level 1: Finished Goods GAP**
            - Supply (Inventory + CAN + Transfer + PO) vs Demand (OC + Forecast)
            - Safety stock consideration
            - Customer impact analysis
            
            **Level 2: Raw Material GAP**
            - BOM explosion for manufacturing products
            - Alternative material analysis
            - Existing MO demand integration
            
            **Product Classification**
            - 🏭 **Manufacturing**: Products with BOM - can be produced
            - 🛒 **Trading**: Products without BOM - need to purchase
            
            **Action Recommendations**
            - 🏭 MO suggestions (for manufacturing with sufficient raw)
            - 🛒 PO-FG suggestions (for trading products)
            - 📦 PO-Raw suggestions (for raw material shortage)
            """)
        st.stop()
    
    # KPI Cards
    st.subheader("📈 Key Metrics")
    render_kpi_cards(result)
    
    st.divider()
    
    # Main Analysis Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 FG Overview",
        "🏭 Manufacturing",
        "🛒 Trading",
        "🧪 Raw Materials",
        "📋 Actions"
    ])
    
    # Tab 1: FG Overview
    with tab1:
        st.subheader("📊 Finished Goods GAP")
        
        # Visual Analysis
        col1, col2 = st.columns(2)
        with col1:
            fig = charts.create_status_donut(result.fg_gap_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = charts.create_value_analysis(result.fg_gap_df)
            st.plotly_chart(fig, use_container_width=True)
        
        # Status summary
        render_status_summary(result.fg_gap_df, key_prefix="fg")
        
        # Quick filter
        quick_filter = render_quick_filter(key_prefix="fg")
        filtered_df = apply_quick_filter(result.fg_gap_df, quick_filter)
        
        # Table controls
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            items_per_page = st.selectbox(
                "Items per page",
                UI_CONFIG['items_per_page_options'],
                index=1,
                key="fg_items_per_page"
            )
        with col2:
            search = st.text_input("Search", placeholder="Filter...", key="fg_search")
            if search:
                mask = filtered_df.astype(str).apply(
                    lambda x: x.str.contains(search, case=False, na=False)
                ).any(axis=1)
                filtered_df = filtered_df[mask]
        
        # Table
        page_info = render_fg_table(filtered_df, items_per_page, state.get_page('fg'))
        
        if page_info:
            new_page = render_pagination(page_info['page'], page_info['total_pages'], "fg")
            if new_page != page_info['page']:
                state.set_page(new_page, 'fg', page_info['total_pages'])
                st.rerun()
    
    # Tab 2: Manufacturing
    with tab2:
        st.subheader("🏭 Manufacturing Products")
        
        if result.has_classification():
            col1, col2 = st.columns(2)
            with col1:
                fig = charts.create_classification_pie(
                    len(result.manufacturing_df),
                    len(result.trading_df)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                metrics = result.get_metrics()
                st.metric("Total Manufacturing", metrics.get('manufacturing_count', 0))
                st.metric("With Shortage", len(result.get_manufacturing_shortage()))
        
        render_manufacturing_table(result)
    
    # Tab 3: Trading
    with tab3:
        st.subheader("🛒 Trading Products")
        render_trading_table(result)
    
    # Tab 4: Raw Materials
    with tab4:
        st.subheader("🧪 Raw Material GAP")
        
        if result.has_raw_data():
            col1, col2 = st.columns(2)
            with col1:
                fig = charts.create_raw_material_status(result.raw_gap_df)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                raw_metrics = result.raw_metrics
                st.metric("Total Materials", raw_metrics.get('total_materials', 0))
                st.metric("With Shortage", raw_metrics.get('shortage_count', 0))
                st.metric("Sufficient", raw_metrics.get('sufficient_count', 0))
            
            render_raw_material_table(result)
        else:
            st.info("No raw material data available")
    
    # Tab 5: Actions
    with tab5:
        st.subheader("📋 Action Recommendations")
        
        if result.has_actions():
            metrics = result.get_metrics()
            
            col1, col2 = st.columns(2)
            with col1:
                fig = charts.create_action_summary(
                    metrics.get('mo_count', 0),
                    metrics.get('po_fg_count', 0),
                    metrics.get('po_raw_count', 0)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Action sub-tabs
            action_tab1, action_tab2, action_tab3 = st.tabs([
                f"🏭 MO ({metrics.get('mo_count', 0)})",
                f"🛒 PO-FG ({metrics.get('po_fg_count', 0)})",
                f"📦 PO-Raw ({metrics.get('po_raw_count', 0)})"
            ])
            
            with action_tab1:
                render_action_table(result, action_type='mo')
            
            with action_tab2:
                render_action_table(result, action_type='po_fg')
            
            with action_tab3:
                render_action_table(result, action_type='po_raw')
        else:
            st.success("✅ No actions required")
    
    st.divider()
    
    # Export section
    st.subheader("📥 Export")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("📥 Export Excel", type="primary", use_container_width=True):
            try:
                excel_data = export_to_excel(result, filter_values)
                filename = get_export_filename()
                
                st.download_button(
                    label="📥 Download",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                logger.error(f"Export failed: {e}")
                st.error("Export failed")
    
    # Footer
    st.divider()
    st.caption(
        f"Last calculated: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Supply Chain GAP Analysis v{VERSION}"
    )


if __name__ == "__main__":
    main()