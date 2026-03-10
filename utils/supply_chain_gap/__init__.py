# utils/supply_chain_gap/__init__.py

"""
Supply Chain GAP Analysis Module
Independent module for full multi-level analysis

Version: 2.1.0

Features:
- Level 1: FG/Output Product GAP
- Level 2: Raw Material GAP (multi-level BOM)
- Product Classification (Manufacturing vs Trading)
- BOM Explosion with Alternatives
- Action Recommendations (MO, PO-FG, PO-Raw)
- @st.fragment per tab (no full-page reruns)
- @st.dialog drill-down (row selection → modal)
"""

from .constants import (
    VERSION,
    GAP_CATEGORIES,
    THRESHOLDS,
    STATUS_CONFIG,
    SUPPLY_SOURCES,
    DEMAND_SOURCES,
    PRODUCT_TYPES,
    BOM_TYPES,
    MATERIAL_TYPES,
    MATERIAL_CATEGORIES,
    MAX_BOM_LEVELS,
    ACTION_TYPES,
    RAW_MATERIAL_STATUS,
    UI_CONFIG,
    FIELD_TOOLTIPS,
    FORMULA_HELP,
    EXPORT_CONFIG
)

from .state import (
    SupplyChainStateManager,
    get_state
)

from .data_loader import (
    SupplyChainDataLoader,
    get_data_loader
)

from .result import (
    SupplyChainGAPResult,
    CustomerImpact,
    ActionRecommendation
)

from .calculator import (
    SupplyChainGAPCalculator,
    get_calculator
)

from .filters import (
    SupplyChainFilters,
    get_filters
)

from .components import (
    # KPI & Status
    render_kpi_cards,
    render_status_summary,
    render_data_freshness,
    
    # Quick Filter
    render_quick_filter,
    apply_quick_filter,
    
    # Tables
    render_fg_table,
    render_manufacturing_table,
    render_trading_table,
    render_raw_material_table,
    render_semi_finished_table,
    render_action_table,
    render_pagination,
    
    # Drill-Down Dialog
    show_product_detail_dialog,
    
    # Fragment wrappers (v2.1)
    fg_charts_fragment,
    fg_table_fragment,
    manufacturing_fragment,
    trading_fragment,
    raw_materials_fragment,
    actions_fragment,
)

from .help import (
    render_help_dialog,
    render_help_tab,
    render_help_popover,
    render_formula_help_section,
    render_field_tooltip
)

from .charts import (
    SupplyChainCharts,
    get_charts
)

from .formatters import (
    SupplyChainFormatter,
    get_formatter
)

from .export import (
    export_to_excel,
    get_export_filename
)

__version__ = VERSION

__all__ = [
    # Version
    '__version__',
    'VERSION',
    
    # Constants
    'GAP_CATEGORIES',
    'THRESHOLDS',
    'STATUS_CONFIG',
    'SUPPLY_SOURCES',
    'DEMAND_SOURCES',
    'PRODUCT_TYPES',
    'BOM_TYPES',
    'MATERIAL_TYPES',
    'MATERIAL_CATEGORIES',
    'MAX_BOM_LEVELS',
    'ACTION_TYPES',
    'RAW_MATERIAL_STATUS',
    'UI_CONFIG',
    'FIELD_TOOLTIPS',
    'FORMULA_HELP',
    'EXPORT_CONFIG',
    
    # State
    'SupplyChainStateManager',
    'get_state',
    
    # Data Loader
    'SupplyChainDataLoader',
    'get_data_loader',
    
    # Result
    'SupplyChainGAPResult',
    'CustomerImpact',
    'ActionRecommendation',
    
    # Calculator
    'SupplyChainGAPCalculator',
    'get_calculator',
    
    # Filters
    'SupplyChainFilters',
    'get_filters',
    
    # Components — individual
    'render_kpi_cards',
    'render_status_summary',
    'render_data_freshness',
    'render_quick_filter',
    'apply_quick_filter',
    'render_fg_table',
    'render_manufacturing_table',
    'render_trading_table',
    'render_raw_material_table',
    'render_semi_finished_table',
    'render_action_table',
    'render_pagination',
    
    # Drill-Down Dialog
    'show_product_detail_dialog',
    
    # Fragment wrappers (v2.1)
    'fg_charts_fragment',
    'fg_table_fragment',
    'manufacturing_fragment',
    'trading_fragment',
    'raw_materials_fragment',
    'actions_fragment',
    
    # Help
    'render_help_dialog',
    'render_help_tab',
    'render_help_popover',
    'render_formula_help_section',
    'render_field_tooltip',
    
    # Charts
    'SupplyChainCharts',
    'get_charts',
    
    # Formatters
    'SupplyChainFormatter',
    'get_formatter',
    
    # Export
    'export_to_excel',
    'get_export_filename'
]