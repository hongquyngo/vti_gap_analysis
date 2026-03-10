# utils/supply_chain_gap/charts.py

"""
Charts for Supply Chain GAP Analysis
Plotly visualizations
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import logging

from .constants import GAP_CATEGORIES, STATUS_CONFIG, PRODUCT_TYPES, UI_CONFIG

logger = logging.getLogger(__name__)


class SupplyChainCharts:
    """Chart generator for Supply Chain GAP Analysis"""
    
    def __init__(self):
        self.chart_height = UI_CONFIG.get('chart_height_compact', 300)
    
    def create_status_donut(self, gap_df: pd.DataFrame, title: str = "GAP Status Distribution") -> go.Figure:
        """Create donut chart for GAP status distribution"""
        
        if gap_df.empty or 'gap_group' not in gap_df.columns:
            return self._empty_chart("No data available")
        
        # Group by category
        group_counts = gap_df['gap_group'].value_counts()
        
        colors = [GAP_CATEGORIES.get(g, {}).get('color', '#6B7280') for g in group_counts.index]
        
        fig = go.Figure(data=[go.Pie(
            labels=group_counts.index,
            values=group_counts.values,
            hole=0.5,
            marker_colors=colors,
            textinfo='label+value',
            textposition='outside'
        )])
        
        fig.update_layout(
            title=title,
            height=self.chart_height,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            margin=dict(t=40, b=40, l=20, r=20)
        )
        
        return fig
    
    def create_classification_pie(self, manufacturing_count: int, trading_count: int) -> go.Figure:
        """Create pie chart for product classification"""
        
        labels = ['Manufacturing', 'Trading']
        values = [manufacturing_count, trading_count]
        colors = [PRODUCT_TYPES['MANUFACTURING']['color'], PRODUCT_TYPES['TRADING']['color']]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors,
            textinfo='label+value+percent',
            textposition='inside'
        )])
        
        fig.update_layout(
            title="Product Classification",
            height=self.chart_height,
            showlegend=False,
            margin=dict(t=40, b=20, l=20, r=20)
        )
        
        return fig
    
    def create_top_items_bar(
        self,
        gap_df: pd.DataFrame,
        item_type: str = 'shortage',
        top_n: int = 10
    ) -> go.Figure:
        """Create bar chart for top shortage/surplus items"""
        
        if gap_df.empty or 'net_gap' not in gap_df.columns:
            return self._empty_chart("No data available")
        
        if item_type == 'shortage':
            filtered = gap_df[gap_df['net_gap'] < 0].nsmallest(top_n, 'net_gap')
            color = '#DC2626'
            title = f"Top {top_n} Shortages"
        else:
            filtered = gap_df[gap_df['net_gap'] > 0].nlargest(top_n, 'net_gap')
            color = '#3B82F6'
            title = f"Top {top_n} Surplus"
        
        if filtered.empty:
            return self._empty_chart(f"No {item_type} items")
        
        # Use pt_code or product_name
        x_col = 'pt_code' if 'pt_code' in filtered.columns else 'product_name'
        
        fig = go.Figure(data=[go.Bar(
            x=filtered[x_col],
            y=filtered['net_gap'],
            marker_color=color,
            text=filtered['net_gap'].apply(lambda x: f"{x:,.0f}"),
            textposition='outside'
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title="Product",
            yaxis_title="Net GAP",
            height=self.chart_height,
            margin=dict(t=40, b=80, l=60, r=20),
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_value_analysis(self, gap_df: pd.DataFrame) -> go.Figure:
        """Create value at risk analysis chart"""
        
        if gap_df.empty or 'at_risk_value' not in gap_df.columns:
            return self._empty_chart("No value data available")
        
        # Top 10 by at risk value
        top_risk = gap_df.nlargest(10, 'at_risk_value')
        
        if top_risk.empty:
            return self._empty_chart("No at-risk items")
        
        x_col = 'pt_code' if 'pt_code' in top_risk.columns else 'product_name'
        
        fig = go.Figure(data=[go.Bar(
            x=top_risk[x_col],
            y=top_risk['at_risk_value'],
            marker_color='#F59E0B',
            text=top_risk['at_risk_value'].apply(lambda x: f"${x:,.0f}"),
            textposition='outside'
        )])
        
        fig.update_layout(
            title="Top 10 At-Risk Value",
            xaxis_title="Product",
            yaxis_title="At Risk Value (USD)",
            height=self.chart_height,
            margin=dict(t=40, b=80, l=60, r=20),
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_raw_material_status(self, raw_gap_df: pd.DataFrame) -> go.Figure:
        """Create raw material status chart — shortage severity distribution"""
        
        if raw_gap_df.empty or 'gap_status' not in raw_gap_df.columns:
            return self._empty_chart("No raw material data")
        
        # Group into meaningful categories for procurement/planning
        def _classify(status):
            if 'CRITICAL' in status or 'SEVERE' in status:
                return '🔴 Critical/Severe'
            elif 'HIGH' in status or 'MODERATE' in status:
                return '🟠 High/Moderate'
            elif 'LIGHT' in status and 'SHORTAGE' in status:
                return '🟡 Light Shortage'
            elif 'BALANCED' in status:
                return '✅ Balanced'
            elif 'SURPLUS' in status:
                return '🔵 Surplus'
            else:
                return '⚪ No Demand'
        
        raw_gap_df = raw_gap_df.copy()
        raw_gap_df['status_group'] = raw_gap_df['gap_status'].apply(_classify)
        
        # Order: critical first
        order = ['🔴 Critical/Severe', '🟠 High/Moderate', '🟡 Light Shortage',
                 '✅ Balanced', '🔵 Surplus', '⚪ No Demand']
        colors = ['#DC2626', '#EA580C', '#EAB308', '#10B981', '#3B82F6', '#D1D5DB']
        
        group_counts = raw_gap_df['status_group'].value_counts()
        ordered_labels = [o for o in order if o in group_counts.index]
        ordered_values = [group_counts[o] for o in ordered_labels]
        ordered_colors = [colors[order.index(o)] for o in ordered_labels]
        
        fig = go.Figure(data=[go.Pie(
            labels=ordered_labels,
            values=ordered_values,
            hole=0.45,
            marker_colors=ordered_colors,
            textinfo='label+value',
            textposition='outside',
            sort=False
        )])
        
        fig.update_layout(
            title="Material Status Distribution",
            height=self.chart_height,
            showlegend=False,
            margin=dict(t=40, b=20, l=20, r=20)
        )
        
        return fig
    
    def create_raw_material_top_shortage(self, raw_gap_df: pd.DataFrame, top_n: int = 8) -> go.Figure:
        """Create top raw material shortages bar chart"""
        
        if raw_gap_df.empty or 'net_gap' not in raw_gap_df.columns:
            return self._empty_chart("No shortage data")
        
        shortage = raw_gap_df[raw_gap_df['net_gap'] < 0].nsmallest(top_n, 'net_gap')
        if shortage.empty:
            return self._empty_chart("No material shortages")
        
        x_col = 'material_pt_code' if 'material_pt_code' in shortage.columns else 'material_name'
        
        fig = go.Figure(data=[go.Bar(
            x=shortage[x_col],
            y=shortage['net_gap'],
            marker_color='#DC2626',
            text=shortage['net_gap'].apply(lambda x: f"{x:,.0f}"),
            textposition='outside'
        )])
        
        fig.update_layout(
            title=f"Top {top_n} Material Shortages",
            xaxis_title="",
            yaxis_title="Net GAP",
            height=self.chart_height,
            margin=dict(t=40, b=80, l=60, r=20),
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_action_summary(self, mo_count: int, po_fg_count: int, po_raw_count: int) -> go.Figure:
        """Create action summary chart"""
        
        labels = ['MO to Create', 'PO for FG', 'PO for Raw']
        values = [mo_count, po_fg_count, po_raw_count]
        colors = ['#3B82F6', '#10B981', '#8B5CF6']
        
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=values,
            textposition='outside'
        )])
        
        fig.update_layout(
            title="Action Summary",
            xaxis_title="Action Type",
            yaxis_title="Count",
            height=self.chart_height,
            margin=dict(t=40, b=40, l=60, r=20)
        )
        
        return fig
    
    def _empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#6B7280")
        )
        fig.update_layout(
            height=self.chart_height,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig


def get_charts() -> SupplyChainCharts:
    """Get charts instance"""
    return SupplyChainCharts()