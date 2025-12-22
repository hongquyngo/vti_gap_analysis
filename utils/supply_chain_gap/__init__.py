# utils/supply_chain_gap/__init__.py

"""
Supply Chain GAP Analysis Module
Independent module for full multi-level analysis

Version: 1.0.0

Features:
- Level 1: FG/Output Product GAP
- Level 2: Raw Material GAP
- Product Classification (Manufacturing vs Trading)
- BOM Explosion with Alternatives
- Action Recommendations (MO, PO-FG, PO-Raw)
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
    ACTION_TYPES,
    RAW_MATERIAL_STATUS,
    UI_CONFIG,
    FIELD_TOOLTIPS,
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
    render_kpi_cards,
    render_status_summary,
    render_quick_filter,
    apply_quick_filter,
    render_fg_table,
    render_manufacturing_table,
    render_trading_table,
    render_raw_material_table,
    render_action_table,
    render_pagination
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
    'ACTION_TYPES',
    'RAW_MATERIAL_STATUS',
    'UI_CONFIG',
    'FIELD_TOOLTIPS',
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
    
    # Components
    'render_kpi_cards',
    'render_status_summary',
    'render_quick_filter',
    'apply_quick_filter',
    'render_fg_table',
    'render_manufacturing_table',
    'render_trading_table',
    'render_raw_material_table',
    'render_action_table',
    'render_pagination',
    
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
