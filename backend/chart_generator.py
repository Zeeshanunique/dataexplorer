"""
Chart generation module for the Data Explorer app
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

class ChartGenerator:
    """Generate various types of charts based on data and user preferences"""
    
    def __init__(self):
        self.chart_types = {
            "bar": self._create_bar_chart,
            "line": self._create_line_chart,
            "scatter": self._create_scatter_chart,
            "pie": self._create_pie_chart,
            "histogram": self._create_histogram,
            "box": self._create_box_chart
        }
    
    def generate_chart(self, df: pd.DataFrame, chart_type: str = "bar", 
                      x_col: str = None, y_col: str = None, 
                      color_col: str = None, title: str = None) -> go.Figure:
        """Generate chart based on parameters"""
        if df.empty:
            return self._create_empty_chart("No data to display")
        
        # Auto-detect columns if not provided
        if not x_col or not y_col:
            x_col, y_col = self._auto_detect_columns(df)
        
        # Generate chart
        if chart_type in self.chart_types:
            return self.chart_types[chart_type](df, x_col, y_col, color_col, title)
        else:
            return self._create_bar_chart(df, x_col, y_col, color_col, title)
    
    def _create_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                         color_col: str = None, title: str = None) -> go.Figure:
        """Create bar chart"""
        try:
            if color_col and color_col in df.columns:
                fig = px.bar(df, x=x_col, y=y_col, color=color_col, 
                           title=title or f"{y_col} by {x_col}")
            else:
                fig = px.bar(df, x=x_col, y=y_col, 
                           title=title or f"{y_col} by {x_col}")
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                showlegend=True if color_col else False
            )
            return fig
        except Exception as e:
            return self._create_error_chart(f"Error creating bar chart: {str(e)}")
    
    def _create_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                          color_col: str = None, title: str = None) -> go.Figure:
        """Create line chart"""
        try:
            if color_col and color_col in df.columns:
                fig = px.line(df, x=x_col, y=y_col, color=color_col, 
                            title=title or f"{y_col} over {x_col}")
            else:
                fig = px.line(df, x=x_col, y=y_col, 
                            title=title or f"{y_col} over {x_col}")
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                showlegend=True if color_col else False
            )
            return fig
        except Exception as e:
            return self._create_error_chart(f"Error creating line chart: {str(e)}")
    
    def _create_scatter_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                             color_col: str = None, title: str = None) -> go.Figure:
        """Create scatter chart"""
        try:
            if color_col and color_col in df.columns:
                fig = px.scatter(df, x=x_col, y=y_col, color=color_col, 
                               title=title or f"{y_col} vs {x_col}")
            else:
                fig = px.scatter(df, x=x_col, y=y_col, 
                               title=title or f"{y_col} vs {x_col}")
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                showlegend=True if color_col else False
            )
            return fig
        except Exception as e:
            return self._create_error_chart(f"Error creating scatter chart: {str(e)}")
    
    def _create_pie_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                         color_col: str = None, title: str = None) -> go.Figure:
        """Create pie chart"""
        try:
            fig = px.pie(df, names=x_col, values=y_col, 
                        title=title or f"Distribution of {y_col} by {x_col}")
            return fig
        except Exception as e:
            return self._create_error_chart(f"Error creating pie chart: {str(e)}")
    
    def _create_histogram(self, df: pd.DataFrame, x_col: str, y_col: str, 
                         color_col: str = None, title: str = None) -> go.Figure:
        """Create histogram"""
        try:
            if color_col and color_col in df.columns:
                fig = px.histogram(df, x=x_col, color=color_col, 
                                 title=title or f"Distribution of {x_col}")
            else:
                fig = px.histogram(df, x=x_col, 
                                 title=title or f"Distribution of {x_col}")
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title="Count",
                showlegend=True if color_col else False
            )
            return fig
        except Exception as e:
            return self._create_error_chart(f"Error creating histogram: {str(e)}")
    
    def _create_box_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                         color_col: str = None, title: str = None) -> go.Figure:
        """Create box chart"""
        try:
            if color_col and color_col in df.columns:
                fig = px.box(df, x=x_col, y=y_col, color=color_col, 
                           title=title or f"Box plot of {y_col} by {x_col}")
            else:
                fig = px.box(df, x=x_col, y=y_col, 
                           title=title or f"Box plot of {y_col} by {x_col}")
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                showlegend=True if color_col else False
            )
            return fig
        except Exception as e:
            return self._create_error_chart(f"Error creating box chart: {str(e)}")
    
    def _auto_detect_columns(self, df: pd.DataFrame) -> Tuple[str, str]:
        """Auto-detect best columns for x and y axes"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if len(numeric_cols) >= 2:
            return numeric_cols[0], numeric_cols[1]
        elif len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            return categorical_cols[0], numeric_cols[0]
        elif len(df.columns) >= 2:
            return df.columns[0], df.columns[1]
        else:
            return df.columns[0], df.columns[0]
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='white'
        )
        return fig
    
    def _create_error_chart(self, error_message: str) -> go.Figure:
        """Create error chart"""
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error: {error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='white'
        )
        return fig
    
    def suggest_chart_type(self, df: pd.DataFrame, x_col: str, y_col: str) -> str:
        """Suggest best chart type based on data"""
        if df.empty:
            return "bar"
        
        # Check data types
        x_is_numeric = pd.api.types.is_numeric_dtype(df[x_col])
        y_is_numeric = pd.api.types.is_numeric_dtype(df[y_col])
        
        if x_is_numeric and y_is_numeric:
            return "scatter"
        elif not x_is_numeric and y_is_numeric:
            return "bar"
        elif x_is_numeric and not y_is_numeric:
            return "histogram"
        else:
            return "bar"
    
    def create_dashboard(self, df: pd.DataFrame, operations: List[Dict]) -> List[go.Figure]:
        """Create multiple charts for dashboard view"""
        charts = []
        
        if df.empty:
            return [self._create_empty_chart("No data available")]
        
        # Get data info
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Create summary charts
        if len(numeric_cols) >= 1:
            # Distribution of first numeric column
            charts.append(self._create_histogram(df, numeric_cols[0], None, 
                                               title=f"Distribution of {numeric_cols[0]}"))
        
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            # Bar chart of categorical vs numeric
            charts.append(self._create_bar_chart(df, categorical_cols[0], numeric_cols[0],
                                               title=f"{numeric_cols[0]} by {categorical_cols[0]}"))
        
        if len(numeric_cols) >= 2:
            # Scatter plot of two numeric columns
            charts.append(self._create_scatter_chart(df, numeric_cols[0], numeric_cols[1],
                                                   title=f"{numeric_cols[1]} vs {numeric_cols[0]}"))
        
        return charts
