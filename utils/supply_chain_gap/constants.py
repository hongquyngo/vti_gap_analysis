# utils/supply_chain_gap/constants.py

"""
Constants for Supply Chain GAP Analysis
Independent module for full multi-level analysis
"""

# =============================================================================
# VERSION
# =============================================================================
VERSION = "1.0.0"

# =============================================================================
# GAP STATUS CATEGORIES
# =============================================================================
GAP_CATEGORIES = {
    'SHORTAGE': {
        'statuses': [
            'CRITICAL_SHORTAGE',   # coverage < 25%
            'SEVERE_SHORTAGE',     # coverage < 50%
            'HIGH_SHORTAGE',       # coverage < 75%
            'MODERATE_SHORTAGE',   # coverage < 90%
            'LIGHT_SHORTAGE'       # coverage < 100%
        ],
        'color': '#DC2626',
        'label': 'Shortage',
        'icon': '🔴'
    },
    'OPTIMAL': {
        'statuses': ['BALANCED'],
        'color': '#10B981',
        'label': 'Optimal',
        'icon': '✅'
    },
    'SURPLUS': {
        'statuses': [
            'LIGHT_SURPLUS',
            'MODERATE_SURPLUS',
            'HIGH_SURPLUS',
            'SEVERE_SURPLUS'
        ],
        'color': '#3B82F6',
        'label': 'Surplus',
        'icon': '📦'
    },
    'INACTIVE': {
        'statuses': ['NO_DEMAND', 'NO_ACTIVITY'],
        'color': '#9CA3AF',
        'label': 'Inactive',
        'icon': '⭕'
    }
}

# =============================================================================
# THRESHOLDS
# =============================================================================
THRESHOLDS = {
    'shortage': {
        'critical': 0.25,
        'severe': 0.50,
        'high': 0.75,
        'moderate': 0.90,
        'light': 1.00
    },
    'surplus': {
        'light': 1.25,
        'moderate': 1.75,
        'high': 2.50,
        'severe': 2.50
    }
}

# =============================================================================
# STATUS CONFIGURATION
# =============================================================================
STATUS_CONFIG = {
    'CRITICAL_SHORTAGE': {'icon': '🚨', 'color': '#7F1D1D', 'priority': 1},
    'SEVERE_SHORTAGE': {'icon': '🔴', 'color': '#DC2626', 'priority': 1},
    'HIGH_SHORTAGE': {'icon': '🟠', 'color': '#EA580C', 'priority': 2},
    'MODERATE_SHORTAGE': {'icon': '🟡', 'color': '#CA8A04', 'priority': 3},
    'LIGHT_SHORTAGE': {'icon': '⚠️', 'color': '#EAB308', 'priority': 4},
    'BALANCED': {'icon': '✅', 'color': '#10B981', 'priority': 99},
    'LIGHT_SURPLUS': {'icon': '🔵', 'color': '#3B82F6', 'priority': 4},
    'MODERATE_SURPLUS': {'icon': '🟣', 'color': '#8B5CF6', 'priority': 3},
    'HIGH_SURPLUS': {'icon': '🟠', 'color': '#F97316', 'priority': 2},
    'SEVERE_SURPLUS': {'icon': '🔴', 'color': '#DC2626', 'priority': 1},
    'NO_DEMAND': {'icon': '⚪', 'color': '#9CA3AF', 'priority': 99},
    'NO_ACTIVITY': {'icon': '⚪', 'color': '#D1D5DB', 'priority': 99}
}

# =============================================================================
# SUPPLY & DEMAND SOURCES
# =============================================================================
SUPPLY_SOURCES = {
    'INVENTORY': {'label': '📦 Inventory', 'icon': '📦', 'priority': 1},
    'CAN_PENDING': {'label': '📋 CAN Pending', 'icon': '📋', 'priority': 2},
    'WAREHOUSE_TRANSFER': {'label': '🚛 Transfer', 'icon': '🚛', 'priority': 3},
    'PURCHASE_ORDER': {'label': '📝 Purchase Order', 'icon': '📝', 'priority': 4}
}

DEMAND_SOURCES = {
    'OC_PENDING': {'label': '✔ Confirmed Orders', 'icon': '✔', 'priority': 1},
    'FORECAST': {'label': '📊 Forecast', 'icon': '📊', 'priority': 2}
}

# =============================================================================
# PRODUCT CLASSIFICATION
# =============================================================================
PRODUCT_TYPES = {
    'MANUFACTURING': {
        'label': 'Manufacturing',
        'icon': '🏭',
        'color': '#3B82F6',
        'description': 'Products with BOM - can be produced'
    },
    'TRADING': {
        'label': 'Trading',
        'icon': '🛒',
        'color': '#10B981',
        'description': 'Products without BOM - need to purchase'
    }
}

# =============================================================================
# BOM TYPES
# =============================================================================
BOM_TYPES = {
    'CUTTING': {'label': 'Cutting', 'icon': '✂️', 'scrap_rate': 2.0},
    'REPACKING': {'label': 'Repacking', 'icon': '📦', 'scrap_rate': 0.5},
    'KITTING': {'label': 'Kitting', 'icon': '🔧', 'scrap_rate': 0.0},
    'ASSEMBLY': {'label': 'Assembly', 'icon': '🔩', 'scrap_rate': 1.0}
}

# =============================================================================
# MATERIAL TYPES
# =============================================================================
MATERIAL_TYPES = {
    'RAW_MATERIAL': {'label': 'Raw Material', 'icon': '🧪', 'priority': 1},
    'PACKAGING': {'label': 'Packaging', 'icon': '📦', 'priority': 2},
    'CONSUMABLE': {'label': 'Consumable', 'icon': '🔧', 'priority': 3}
}

# =============================================================================
# ACTION TYPES
# =============================================================================
ACTION_TYPES = {
    'CREATE_MO': {
        'label': 'Create MO',
        'icon': '🏭',
        'color': '#3B82F6',
        'category': 'Manufacturing'
    },
    'WAIT_RAW': {
        'label': 'Wait for Raw',
        'icon': '⏳',
        'color': '#F59E0B',
        'category': 'Manufacturing'
    },
    'CREATE_PO_FG': {
        'label': 'Create PO (FG)',
        'icon': '🛒',
        'color': '#10B981',
        'category': 'Purchase'
    },
    'CREATE_PO_RAW': {
        'label': 'Create PO (Raw)',
        'icon': '📦',
        'color': '#8B5CF6',
        'category': 'Purchase'
    },
    'USE_ALTERNATIVE': {
        'label': 'Use Alternative',
        'icon': '🔄',
        'color': '#06B6D4',
        'category': 'Alternative'
    }
}

# =============================================================================
# RAW MATERIAL STATUS
# =============================================================================
RAW_MATERIAL_STATUS = {
    'SUFFICIENT': {'label': 'Sufficient', 'icon': '✅', 'color': '#10B981'},
    'PARTIAL': {'label': 'Partial', 'icon': '⚠️', 'color': '#F59E0B'},
    'ALTERNATIVE_AVAILABLE': {'label': 'Alt Available', 'icon': '🔄', 'color': '#06B6D4'},
    'SHORTAGE': {'label': 'Shortage', 'icon': '🔴', 'color': '#DC2626'},
    'NO_SUPPLY': {'label': 'No Supply', 'icon': '❌', 'color': '#7F1D1D'}
}

# =============================================================================
# UI CONFIGURATION
# =============================================================================
UI_CONFIG = {
    'items_per_page_options': [10, 25, 50, 100],
    'default_items_per_page': 25,
    'max_chart_items': 20,
    'chart_height': 400,
    'chart_height_compact': 300
}

# =============================================================================
# FIELD TOOLTIPS
# =============================================================================
FIELD_TOOLTIPS = {
    'net_gap': 'Available Supply - Total Demand',
    'coverage_ratio': '(Available Supply ÷ Demand) × 100%',
    'at_risk_value': 'Shortage × Selling Price',
    'safety_gap': 'Total Supply - Safety Stock',
    'available_supply': 'MAX(0, Total Supply - Safety Stock)',
    'can_produce': 'Whether raw materials are sufficient for production',
    'limiting_materials': 'Materials causing production bottleneck'
}

# =============================================================================
# EXPORT CONFIGURATION
# =============================================================================
EXPORT_CONFIG = {
    'sheets': [
        'Summary',
        'FG GAP',
        'Manufacturing',
        'Trading',
        'Raw Material GAP',
        'Actions'
    ],
    'max_rows': 10000
}
