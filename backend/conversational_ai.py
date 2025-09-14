"""
Conversational AI module using OpenAI for enhanced natural language processing
"""
import openai
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from config import OPENAI_API_KEY

class ConversationalAI:
    """Enhanced conversational AI for data exploration using OpenAI"""
    
    def __init__(self, data_info: Dict[str, Any]):
        self.data_info = data_info
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.conversation_history = []
        
    def process_conversational_command(self, command: str, current_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Process conversational commands with OpenAI assistance"""
        
        if not self.client:
            return self._fallback_processing(command, current_data)
        
        try:
            # Prepare context for OpenAI
            context = self._prepare_context(current_data)
            
            # Create conversation prompt
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(command, context)
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content
            parsed_response = self._parse_ai_response(ai_response, command)
            
            # Add to conversation history
            self.conversation_history.append({
                "user": command,
                "ai": ai_response,
                "operation": parsed_response.get("operation_type"),
                "confidence": parsed_response.get("confidence", 0.0)
            })
            
            return parsed_response
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._fallback_processing(command, current_data)
    
    def _prepare_context(self, current_data: pd.DataFrame = None) -> str:
        """Prepare context about the current data for OpenAI"""
        context_parts = []
        
        # Basic data info
        context_parts.append(f"Dataset has {self.data_info['shape'][0]:,} rows and {self.data_info['shape'][1]} columns.")
        
        # Column information
        context_parts.append(f"Columns: {', '.join(self.data_info['columns'])}")
        
        # Data types
        if self.data_info['numeric_columns']:
            context_parts.append(f"Numeric columns: {', '.join(self.data_info['numeric_columns'])}")
        
        if self.data_info['categorical_columns']:
            context_parts.append(f"Categorical columns: {', '.join(self.data_info['categorical_columns'])}")
        
        if self.data_info['date_columns']:
            context_parts.append(f"Date columns: {', '.join(self.data_info['date_columns'])}")
        
        # Current data state
        if current_data is not None and not current_data.empty:
            context_parts.append(f"Current view has {len(current_data):,} rows.")
            
            # Sample data for context
            sample_data = current_data.head(3).to_string()
            context_parts.append(f"Sample data:\n{sample_data}")
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for OpenAI"""
        return """You are a helpful data analyst assistant. Your job is to understand user requests about data analysis and convert them into specific operations.

Available operations with exact parameter names:
1. top_n - Get top N items by a column
   Parameters: {"n": int, "sort_column": "column_name", "ascending": boolean}
   Example: "top 5 products by sales" -> {"n": 5, "sort_column": "sales", "ascending": false}

2. filter - Filter data based on conditions
   Parameters: {"column": "column_name", "operator": "equals|not_equals|greater_than|less_than|contains", "value": any}
   Example: "show products with price > 1000" -> {"column": "price", "operator": "greater_than", "value": 1000}

3. group_aggregate - Group data and apply aggregations
   Parameters: {"group_columns": ["col1", "col2"], "agg_dict": {"column": "sum|mean|count|max|min"}}
   Example: "group by region and sum sales" -> {"group_columns": ["region"], "agg_dict": {"sales": "sum"}}

4. sort - Sort data by columns
   Parameters: {"sort_columns": ["col1", "col2"], "ascending": [boolean, boolean]}
   Example: "sort by revenue descending" -> {"sort_columns": ["revenue"], "ascending": [false]}

5. pivot - Create pivot tables
   Parameters: {"index": "row_column", "columns": "col_column", "values": "value_column", "aggfunc": "sum|mean|count"}
   Example: "pivot sales by region and quarter" -> {"index": "region", "columns": "quarter", "values": "sales", "aggfunc": "sum"}

IMPORTANT: Respond with ONLY a JSON object, no additional text. The JSON should contain:
- operation_type: one of the above operations
- operation_params: parameters for the operation (use exact parameter names above)
- confidence: confidence level (0.0 to 1.0)
- explanation: human-readable explanation of what you're doing
- suggestions: array of 2-3 alternative interpretations if the request is ambiguous

Be conversational and helpful. If the request is unclear, provide suggestions for clarification."""
    
    def _create_user_prompt(self, command: str, context: str) -> str:
        """Create user prompt for OpenAI"""
        return f"""User request: "{command}"

Data context:
{context}

Please analyze this request and provide the appropriate operation in JSON format. Be specific about column names and values."""
    
    def _parse_ai_response(self, ai_response: str, original_command: str) -> Dict[str, Any]:
        """Parse OpenAI response and extract operation details"""
        try:
            # Try to extract JSON from the response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = ai_response[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Add original command and create clean explanation
                parsed['original_command'] = original_command
                parsed['ai_explanation'] = self._create_clean_explanation(parsed, original_command)
                
                # Convert string suggestions to proper format
                if 'suggestions' in parsed and isinstance(parsed['suggestions'], list):
                    formatted_suggestions = []
                    for suggestion in parsed['suggestions']:
                        if isinstance(suggestion, str):
                            # Convert string to proper format
                            formatted_suggestions.append({
                                "type": "command",
                                "description": suggestion,
                                "operation": {"command": suggestion}
                            })
                        else:
                            formatted_suggestions.append(suggestion)
                    parsed['suggestions'] = formatted_suggestions
                
                return parsed
            else:
                # Fallback if no JSON found
                return self._fallback_processing(original_command)
                
        except json.JSONDecodeError:
            return self._fallback_processing(original_command)
    
    def _create_clean_explanation(self, parsed_response: Dict[str, Any], original_command: str) -> str:
        """Create a clean, user-friendly explanation from the parsed response"""
        explanation = parsed_response.get('explanation', '')
        operation_type = parsed_response.get('operation_type', '')
        confidence = parsed_response.get('confidence', 0.0)
        
        # Create a conversational response
        if operation_type == 'top_n':
            n = parsed_response.get('operation_params', {}).get('n', 5)
            column = parsed_response.get('operation_params', {}).get('sort_column', 'value')
            return f"I'll show you the top {n} items by {column}. This will help you identify the best performing items in your data."
        
        elif operation_type == 'group_aggregate':
            group_cols = parsed_response.get('operation_params', {}).get('group_columns', ['category'])
            return f"I'll group your data by {', '.join(group_cols)} and show you the aggregated results. This will help you see patterns and trends."
        
        elif operation_type == 'filter':
            column = parsed_response.get('operation_params', {}).get('column', 'data')
            operator = parsed_response.get('operation_params', {}).get('operator', 'equals')
            value = parsed_response.get('operation_params', {}).get('value', 'criteria')
            return f"I'll filter your data to show only items where {column} {operator} {value}. This will help you focus on specific subsets of your data."
        
        elif operation_type == 'sort':
            columns = parsed_response.get('operation_params', {}).get('columns', ['value'])
            ascending = parsed_response.get('operation_params', {}).get('ascending', [False])[0]
            direction = "ascending" if ascending else "descending"
            return f"I'll sort your data by {', '.join(columns)} in {direction} order. This will help you see the data organized by your chosen criteria."
        
        elif operation_type == 'pivot':
            index = parsed_response.get('operation_params', {}).get('index', 'category')
            columns = parsed_response.get('operation_params', {}).get('columns', 'subcategory')
            values = parsed_response.get('operation_params', {}).get('values', 'value')
            return f"I'll create a pivot table showing {values} by {index} and {columns}. This will help you see cross-tabulated data in a clear format."
        
        else:
            return explanation or "I'll help you analyze your data. Let me process your request."
    
    def _fallback_processing(self, command: str, current_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Fallback processing when OpenAI is not available"""
        command_lower = command.lower()
        
        # Simple pattern matching as fallback
        if "top" in command_lower and any(char.isdigit() for char in command):
            # Extract number
            import re
            numbers = re.findall(r'\d+', command)
            n = int(numbers[0]) if numbers else 5
            
            # Find best column for sorting
            sort_column = self.data_info['numeric_columns'][0] if self.data_info['numeric_columns'] else self.data_info['columns'][0]
            
            return {
                "original_command": command,
                "operation_type": "top_n",
                "operation_params": {
                    "n": n,
                    "sort_column": sort_column,
                    "ascending": "lowest" in command_lower or "worst" in command_lower
                },
                "confidence": 0.6,
                "explanation": f"I'll show you the top {n} items by {sort_column}. This will help you identify the best performing items in your data.",
                "ai_explanation": f"I'll show you the top {n} items by {sort_column}. This will help you identify the best performing items in your data.",
                "suggestions": self._generate_fallback_suggestions()
            }
        
        elif "group" in command_lower and "by" in command_lower:
            # Find group column
            group_cols = []
            for col in self.data_info['categorical_columns']:
                if col.lower() in command_lower:
                    group_cols.append(col)
            
            if not group_cols:
                group_cols = [self.data_info['categorical_columns'][0]] if self.data_info['categorical_columns'] else [self.data_info['columns'][0]]
            
            return {
                "original_command": command,
                "operation_type": "group_aggregate",
                "operation_params": {
                    "group_columns": group_cols,
                    "agg_dict": {"count": "size"}
                },
                "confidence": 0.6,
                "explanation": f"I'll group your data by {', '.join(group_cols)} and show you the aggregated results. This will help you see patterns and trends.",
                "ai_explanation": f"I'll group your data by {', '.join(group_cols)} and show you the aggregated results. This will help you see patterns and trends.",
                "suggestions": self._generate_fallback_suggestions()
            }
        
        elif "product" in command_lower and ("top" in command_lower or "best" in command_lower or "selling" in command_lower):
            # Special handling for product-related queries
            sort_column = 'net_revenue' if 'net_revenue' in self.data_info['numeric_columns'] else self.data_info['numeric_columns'][0]
            return {
                "original_command": command,
                "operation_type": "top_n",
                "operation_params": {
                    "n": 5,
                    "sort_column": sort_column,
                    "ascending": False
                },
                "confidence": 0.7,
                "explanation": f"I'll show you the top 5 products by {sort_column}. This will help you identify your best selling products.",
                "ai_explanation": f"I'll show you the top 5 products by {sort_column}. This will help you identify your best selling products.",
                "suggestions": self._generate_fallback_suggestions()
            }
        
        else:
            return {
                "original_command": command,
                "operation_type": None,
                "operation_params": {},
                "confidence": 0.1,
                "explanation": "I'm not sure what you'd like me to do. Could you be more specific?",
                "ai_explanation": "I'm not sure what you'd like me to do. Could you be more specific?",
                "suggestions": self._generate_fallback_suggestions()
            }
    
    def _generate_fallback_suggestions(self) -> List[Dict[str, str]]:
        """Generate fallback suggestions when OpenAI is not available"""
        suggestions = []
        
        if self.data_info.get('numeric_columns'):
            suggestions.append({
                "type": "top_n",
                "description": f"Show top 5 by {self.data_info['numeric_columns'][0]}",
                "operation": {"n": 5, "sort_column": self.data_info['numeric_columns'][0], "ascending": False}
            })
        
        if self.data_info.get('categorical_columns'):
            suggestions.append({
                "type": "group_aggregate",
                "description": f"Group by {self.data_info['categorical_columns'][0]}",
                "operation": {"group_columns": [self.data_info['categorical_columns'][0]], "agg_dict": {"gross_revenue": "sum"}}
            })
        
        if len(self.data_info.get('numeric_columns', [])) >= 2:
            suggestions.append({
                "type": "correlation",
                "description": f"Show correlation between {self.data_info['numeric_columns'][0]} and {self.data_info['numeric_columns'][1]}",
                "operation": {"type": "correlation", "columns": [self.data_info['numeric_columns'][0], self.data_info['numeric_columns'][1]]}
            })
        
        return suggestions[:3]
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation so far"""
        if not self.conversation_history:
            return "No conversation yet. Ask me anything about your data!"
        
        summary_parts = []
        summary_parts.append(f"We've had {len(self.conversation_history)} exchanges so far.")
        
        # Count operations
        operations = [conv['operation'] for conv in self.conversation_history if conv['operation']]
        if operations:
            from collections import Counter
            op_counts = Counter(operations)
            summary_parts.append(f"Operations performed: {dict(op_counts)}")
        
        return " ".join(summary_parts)
    
    def get_suggested_follow_ups(self, current_data: pd.DataFrame = None) -> List[str]:
        """Get suggested follow-up questions based on current data"""
        suggestions = []
        
        if current_data is not None and not current_data.empty:
            # Based on current data state
            if len(current_data) < 100:
                suggestions.append("Show me more details about this data")
            elif len(current_data) > 1000:
                suggestions.append("Let me see a summary of this data")
            
            # Based on columns
            numeric_cols = current_data.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                suggestions.append(f"Show correlation between {numeric_cols[0]} and {numeric_cols[1]}")
            
            categorical_cols = current_data.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) >= 1:
                suggestions.append(f"Break this down by {categorical_cols[0]}")
        
        # General suggestions
        suggestions.extend([
            "What are the key insights from this data?",
            "Show me the data in a different way",
            "Help me understand what this means"
        ])
        
        return suggestions[:5]
