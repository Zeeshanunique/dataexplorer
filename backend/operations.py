"""
Data operations library for the Data Explorer app
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import re

class DataOperations:
    """Core data operations for filtering, sorting, grouping, and aggregating data"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_df = df.copy()
        self.operation_history = []
    
    def reset(self):
        """Reset to original data"""
        self.df = self.original_df.copy()
        self.operation_history = []
    
    def filter_data(self, column: str, operator: str, value: Any, description: str = "") -> pd.DataFrame:
        """Filter data based on column, operator, and value"""
        try:
            if operator == "equals":
                result = self.df[self.df[column] == value]
            elif operator == "not_equals":
                result = self.df[self.df[column] != value]
            elif operator == "greater_than":
                result = self.df[self.df[column] > value]
            elif operator == "less_than":
                result = self.df[self.df[column] < value]
            elif operator == "greater_equal":
                result = self.df[self.df[column] >= value]
            elif operator == "less_equal":
                result = self.df[self.df[column] <= value]
            elif operator == "contains":
                result = self.df[self.df[column].astype(str).str.contains(str(value), case=False, na=False)]
            elif operator == "starts_with":
                result = self.df[self.df[column].astype(str).str.startswith(str(value), na=False)]
            elif operator == "ends_with":
                result = self.df[self.df[column].astype(str).str.endswith(str(value), na=False)]
            else:
                return self.df
            
            self.df = result
            self.operation_history.append({
                "operation": "filter",
                "column": column,
                "operator": operator,
                "value": value,
                "description": description or f"Filtered {column} {operator} {value}",
                "rows_before": len(self.original_df),
                
                "rows_after": len(result)
            })
            return result
        except Exception as e:
            return self.df
    
    def sort_data(self, columns: List[str], ascending: List[bool] = None, description: str = "") -> pd.DataFrame:
        """Sort data by specified columns"""
        try:
            if ascending is None:
                ascending = [True] * len(columns)
            
            result = self.df.sort_values(by=columns, ascending=ascending)
            self.df = result
            self.operation_history.append({
                "operation": "sort",
                "columns": columns,
                "ascending": ascending,
                "description": description or f"Sorted by {', '.join(columns)}",
                "rows": len(result)
            })
            return result
        except Exception as e:
            return self.df
    
    def group_and_aggregate(self, group_columns: List[str], agg_dict: Dict[str, str], description: str = "") -> pd.DataFrame:
        """Group data and apply aggregations"""
        try:
            result = self.df.groupby(group_columns).agg(agg_dict).reset_index()
            self.df = result
            self.operation_history.append({
                "operation": "group_aggregate",
                "group_columns": group_columns,
                "agg_dict": agg_dict,
                "description": description or f"Grouped by {', '.join(group_columns)} and aggregated",
                "rows_before": len(self.original_df),
                "rows_after": len(result)
            })
            return result
        except Exception as e:
            return self.df
    
    def pivot_table(self, index: str, columns: str, values: str, aggfunc: str = "sum", description: str = "") -> pd.DataFrame:
        """Create pivot table"""
        try:
            result = self.df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc, fill_value=0)
            self.df = result
            self.operation_history.append({
                "operation": "pivot",
                "index": index,
                "columns": columns,
                "values": values,
                "aggfunc": aggfunc,
                "description": description or f"Pivoted {values} by {index} and {columns}",
                "rows_before": len(self.original_df),
                "rows_after": len(result)
            })
            return result
        except Exception as e:
            return self.df
    
    def get_top_n(self, n: int, sort_column: str, ascending: bool = False, description: str = "") -> pd.DataFrame:
        """Get top N rows by a column"""
        try:
            result = self.df.nlargest(n, sort_column) if not ascending else self.df.nsmallest(n, sort_column)
            self.df = result
            self.operation_history.append({
                "operation": "top_n",
                "n": n,
                "sort_column": sort_column,
                "ascending": ascending,
                "description": description or f"Top {n} by {sort_column}",
                "rows": len(result)
            })
            return result
        except Exception as e:
            return self.df
    
    def select_columns(self, columns: List[str], description: str = "") -> pd.DataFrame:
        """Select specific columns"""
        try:
            result = self.df[columns]
            self.df = result
            self.operation_history.append({
                "operation": "select_columns",
                "columns": columns,
                "description": description or f"Selected columns: {', '.join(columns)}",
                "rows": len(result)
            })
            return result
        except Exception as e:
            return self.df
    
    def get_data_info(self) -> Dict[str, Any]:
        """Get information about current data"""
        return {
            "shape": self.df.shape,
            "columns": list(self.df.columns),
            "dtypes": self.df.dtypes.to_dict(),
            "null_counts": self.df.isnull().sum().to_dict(),
            "numeric_columns": self.df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": self.df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "date_columns": self.df.select_dtypes(include=['datetime64']).columns.tolist()
        }
    
    def get_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Generate suggestions based on query and data"""
        suggestions = []
        data_info = self.get_data_info()
        
        # Common patterns and suggestions
        if "top" in query.lower() and "5" in query:
            if data_info["numeric_columns"]:
                suggestions.append({
                    "type": "top_n",
                    "description": f"Show top 5 by {data_info['numeric_columns'][0]}",
                    "operation": {"n": 5, "sort_column": data_info["numeric_columns"][0], "ascending": False}
                })
        
        if "season" in query.lower() or "quarter" in query.lower():
            if data_info["date_columns"]:
                suggestions.append({
                    "type": "group_aggregate",
                    "description": f"Group by quarter using {data_info['date_columns'][0]}",
                    "operation": {"group_columns": [data_info["date_columns"][0]], "agg_dict": {"count": "size"}}
                })
        
        if "region" in query.lower():
            categorical_cols = [col for col in data_info["categorical_columns"] if "region" in col.lower() or "location" in col.lower()]
            if categorical_cols:
                suggestions.append({
                    "type": "group_aggregate",
                    "description": f"Group by {categorical_cols[0]}",
                    "operation": {"group_columns": [categorical_cols[0]], "agg_dict": {"count": "size"}}
                })
        
        return suggestions[:3]  # Return top 3 suggestions
