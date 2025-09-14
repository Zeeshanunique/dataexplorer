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
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content
            print(f"AI Response for '{command}': {ai_response}")
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
        return """You are an expert data analyst assistant specializing in business intelligence and data exploration. Your role is to understand natural language requests about data analysis and convert them into precise, executable operations.

## CORE PRINCIPLES:
- Think like a business analyst who understands both technical operations and business context
- Always consider the user's intent, not just their exact words
- Provide actionable insights and clear explanations
- Be conversational yet precise in your analysis

## AVAILABLE OPERATIONS (use exact parameter names):

### 1. TOP_N - Get top/bottom N items by a column
**Parameters:** {"n": int, "sort_column": "column_name", "ascending": boolean}
**Use for:** Rankings, best/worst performers, top products, highest values
**Examples:**
- "top 5 products by sales" → {"n": 5, "sort_column": "sales", "ascending": false}
- "bottom 10 regions by revenue" → {"n": 10, "sort_column": "revenue", "ascending": true}
- "show me the top 3" → {"n": 3, "sort_column": "gross_revenue", "ascending": false}

### 2. FILTER - Filter data based on conditions
**Parameters:** {"column": "column_name", "operator": "equals|not_equals|greater_than|less_than|greater_equal|less_equal|contains|starts_with|ends_with", "value": any}
**Use for:** Specific conditions, date ranges, category filters, value thresholds
**Examples:**
- "show products with price > 1000" → {"column": "price", "operator": "greater_than", "value": 1000}
- "filter by region = West" → {"column": "region", "operator": "equals", "value": "West"}
- "products containing 'Pro'" → {"column": "product_name", "operator": "contains", "value": "Pro"}

### 3. GROUP_AGGREGATE - Group data and apply aggregations
**Parameters:** {"group_columns": ["col1", "col2"], "agg_dict": {"column": "sum|mean|count|max|min|avg"}}
**Use for:** Summaries, aggregations, rollups, category analysis
**Examples:**
- "group by region and sum sales" → {"group_columns": ["region"], "agg_dict": {"sales": "sum"}}
- "average revenue by quarter" → {"group_columns": ["quarter"], "agg_dict": {"revenue": "mean"}}
- "count products by category" → {"group_columns": ["category"], "agg_dict": {"product_id": "count"}}

### 4. SORT - Sort data by columns
**Parameters:** {"columns": ["col1", "col2"], "ascending": [boolean, boolean]}
**Use for:** Ordering data, ranking, chronological sorting
**Examples:**
- "sort by revenue descending" → {"columns": ["revenue"], "ascending": [false]}
- "order by date and then by amount" → {"columns": ["date", "amount"], "ascending": [true, false]}

### 5. PIVOT - Create pivot tables
**Parameters:** {"index": "row_column", "columns": "col_column", "values": "value_column", "aggfunc": "sum|mean|count|max|min"}
**Use for:** Cross-tabulation, matrix views, multi-dimensional analysis
**Examples:**
- "pivot sales by region and quarter" → {"index": "region", "columns": "quarter", "values": "sales", "aggfunc": "sum"}
- "create a pivot of revenue by product and channel" → {"index": "product", "columns": "channel", "values": "revenue", "aggfunc": "sum"}

### 6. CORRELATION - Analyze correlation between columns
**Parameters:** {"columns": ["col1", "col2"], "method": "pearson|spearman|kendall"}
**Use for:** Correlation analysis, relationship discovery, dependency analysis
**Examples:**
- "correlation between discount and sales" → {"columns": ["discount_pct", "units_sold"], "method": "pearson"}
- "analyze relationship between price and revenue" → {"columns": ["unit_price", "gross_revenue"], "method": "pearson"}

## RESPONSE FORMAT:
Respond with ONLY a JSON object containing:
- **operation_type**: One of the above operations (or null if unclear)
- **operation_params**: Parameters using exact names above
- **confidence**: Confidence level 0.0-1.0
- **explanation**: Detailed, conversational explanation that directly addresses the user's query with business context
- **suggestions**: Array of 2-3 helpful follow-up suggestions for further analysis

## EXPLANATION GUIDELINES:
- Be conversational and directly address what the user asked
- Provide business context and insights
- Explain what the results will show and why it's useful
- Use specific column names and values from the user's query
- Make it sound like a helpful business analyst, not a technical system
- ALWAYS generate unique, contextual explanations that directly respond to the specific query
- NEVER use generic responses - each explanation should be tailored to the exact question asked

## INTELLIGENT ANALYSIS:
- **Context Awareness**: Use column names and data types from the dataset
- **Business Logic**: Understand common business metrics (revenue, profit, growth, etc.)
- **Ambiguity Handling**: When unclear, provide multiple interpretations
- **Default Values**: Use sensible defaults (e.g., top 5 if "top" without number)
- **Column Matching**: Match user terms to actual column names intelligently

## EXAMPLES OF SMART INTERPRETATIONS:
- "show me the best performers" → top_n with revenue/gross_revenue
- "what's trending" → sort by date descending or top_n by growth
- "breakdown by region" → group_aggregate by region
- "compare quarters" → pivot by quarter or group by quarter
- "revenue analysis" → group_aggregate with sum of revenue columns

Be conversational, insightful, and always consider the business context of the data analysis request."""
    
    def _create_user_prompt(self, command: str, context: str) -> str:
        """Create user prompt for OpenAI"""
        return f"""## USER REQUEST:
"{command}"

## DATASET CONTEXT:
{context}

## ANALYSIS TASK:
Analyze the user's request and determine the most appropriate data operation. Consider:
1. What is the user trying to achieve?
2. Which columns are most relevant?
3. What operation best matches their intent?
4. Are there any ambiguities that need clarification?

## INSTRUCTIONS:
- Use the exact column names from the dataset context
- Choose the most appropriate operation type
- Provide sensible defaults for missing parameters
- If the request is ambiguous, provide multiple suggestions
- Consider business context and common data analysis patterns

Respond with a JSON object following the specified format."""
    
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
                else:
                    # Generate suggestions if none provided by AI
                    parsed['suggestions'] = self._generate_fallback_suggestions()
                
                return parsed
            else:
                # Fallback if no JSON found
                return self._fallback_processing(original_command)
                
        except json.JSONDecodeError:
            return self._fallback_processing(original_command)
    
    def _create_clean_explanation(self, parsed_response: Dict[str, Any], original_command: str) -> str:
        """Create a contextual, conversational explanation from the parsed response"""
        explanation = parsed_response.get('explanation', '')
        operation_type = parsed_response.get('operation_type', '')
        confidence = parsed_response.get('confidence', 0.0)
        operation_params = parsed_response.get('operation_params', {})
        
        # Use the AI's explanation if it exists and is meaningful
        if explanation and len(explanation.strip()) > 20:
            return explanation
        
        # Fallback to contextual responses only if AI didn't provide a good explanation
        command_lower = original_command.lower()
        
        if operation_type == 'top_n':
            n = operation_params.get('n', 5)
            column = operation_params.get('sort_column', 'value')
            ascending = operation_params.get('ascending', False)
            
            # Contextual responses based on user query
            if 'product' in command_lower:
                if ascending:
                    return f"Here are the {n} lowest performing products by {column}. This shows which products might need attention or improvement."
                else:
                    return f"Here are your top {n} performing products by {column}. These are your best sellers and highest revenue generators."
            
            elif 'region' in command_lower or 'area' in command_lower:
                if ascending:
                    return f"Here are the {n} regions with the lowest {column}. This helps identify underperforming markets."
                else:
                    return f"Here are the top {n} regions by {column}. This shows your strongest performing markets."
            
            elif 'revenue' in command_lower or 'sales' in command_lower:
                if ascending:
                    return f"Here are the {n} items with the lowest {column}. This helps identify areas that need improvement."
                else:
                    return f"Here are the top {n} items by {column}. These represent your highest revenue generators."
            
            elif 'best' in command_lower or 'top' in command_lower:
                return f"Here are your top {n} performers by {column}. These are the standout items in your dataset."
            
            elif 'worst' in command_lower or 'lowest' in command_lower:
                return f"Here are the {n} lowest performers by {column}. These items may need attention or improvement."
            
            else:
                # Generic but contextual response
                direction = "lowest" if ascending else "highest"
                return f"I've found the {n} items with the {direction} {column} values. This gives you a clear view of the {direction} performing items in your data."
        
        elif operation_type == 'group_aggregate':
            group_cols = operation_params.get('group_columns', ['category'])
            agg_dict = operation_params.get('agg_dict', {})
            
            # Contextual responses based on user query
            if 'region' in command_lower:
                return f"I've grouped your data by {', '.join(group_cols)} and calculated the totals. This shows you the performance breakdown across different regions, helping you identify which markets are driving your business."
            
            elif 'quarter' in command_lower or 'time' in command_lower or 'trend' in command_lower:
                return f"I've grouped your data by {', '.join(group_cols)} to show trends over time. This reveals seasonal patterns and helps you understand how your business performs across different periods."
            
            elif 'product' in command_lower or 'category' in command_lower:
                return f"I've grouped your data by {', '.join(group_cols)} to show performance by product category. This helps you understand which product lines are contributing most to your revenue."
            
            elif 'sum' in command_lower or 'total' in command_lower:
                return f"I've calculated the totals by {', '.join(group_cols)}. This gives you a clear summary of your data, showing the aggregated values for each group."
            
            else:
                return f"I've grouped your data by {', '.join(group_cols)} and calculated the aggregated results. This reveals patterns and trends in your data that weren't visible before."
        
        elif operation_type == 'filter':
            column = operation_params.get('column', 'data')
            operator = operation_params.get('operator', 'equals')
            value = operation_params.get('value', 'criteria')
            
            # Contextual responses based on user query
            if 'region' in command_lower:
                return f"I've filtered your data to show only {column} = {value}. This focuses your analysis on this specific region, helping you understand its unique characteristics and performance."
            
            elif 'date' in command_lower or 'time' in command_lower:
                return f"I've filtered your data to show only records where {column} {operator} {value}. This narrows your view to a specific time period, making it easier to analyze trends and patterns."
            
            elif 'product' in command_lower:
                return f"I've filtered your data to show only {column} = {value}. This focuses on this specific product or category, giving you detailed insights into its performance."
            
            else:
                return f"I've filtered your data to show only items where {column} {operator} {value}. This helps you focus on a specific subset of your data for more targeted analysis."
        
        elif operation_type == 'sort':
            columns = operation_params.get('columns', ['value'])
            ascending = operation_params.get('ascending', [False])[0]
            direction = "ascending" if ascending else "descending"
            
            # Contextual responses based on user query
            if 'revenue' in command_lower or 'sales' in command_lower:
                return f"I've sorted your data by {', '.join(columns)} in {direction} order. This shows your {'highest' if not ascending else 'lowest'} revenue items first, helping you identify your top performers."
            
            elif 'date' in command_lower or 'time' in command_lower:
                return f"I've sorted your data by {', '.join(columns)} in {direction} order. This organizes your data chronologically, making it easier to see trends and patterns over time."
            
            elif 'product' in command_lower:
                return f"I've sorted your data by {', '.join(columns)} in {direction} order. This ranks your products by performance, showing you which ones are driving the most value."
            
            else:
                return f"I've sorted your data by {', '.join(columns)} in {direction} order. This organizes your data in a logical sequence, making it easier to identify patterns and outliers."
        
        elif operation_type == 'pivot':
            index = operation_params.get('index', 'category')
            columns = operation_params.get('columns', 'subcategory')
            values = operation_params.get('values', 'value')
            
            # Contextual responses based on user query
            if 'region' in command_lower and 'quarter' in command_lower:
                return f"I've created a pivot table showing {values} by {index} and {columns}. This gives you a clear matrix view of how your performance varies across regions and time periods."
            
            elif 'product' in command_lower and 'region' in command_lower:
                return f"I've created a pivot table showing {values} by {index} and {columns}. This reveals which products perform best in which regions, helping you optimize your regional strategy."
            
            else:
                return f"I've created a pivot table showing {values} by {index} and {columns}. This cross-tabulated view reveals relationships between different dimensions of your data that weren't obvious before."
        
        else:
            return explanation or "I'll help you analyze your data. Let me process your request."
    
    def enhance_explanation_with_data_context(self, original_explanation: str, operation_type: str, 
                                            operation_params: Dict[str, Any], data_results: pd.DataFrame, 
                                            original_command: str) -> str:
        """Enhance explanation with actual data context and insights"""
        if data_results.empty:
            return original_explanation
        
        command_lower = original_command.lower()
        data_summary = self._analyze_data_results(data_results, operation_type, operation_params)
        
        # Create enhanced explanation with data insights
        if operation_type == 'top_n':
            n = operation_params.get('n', 5)
            column = operation_params.get('sort_column', 'value')
            ascending = operation_params.get('ascending', False)
            
            # Get actual values from the data
            if not data_results.empty:
                top_value = data_results.iloc[0][column] if column in data_results.columns else 0
                bottom_value = data_results.iloc[-1][column] if column in data_results.columns else 0
                
                if 'product' in command_lower:
                    if ascending:
                        return f"Here are the {n} lowest performing products by {column}. The range goes from {bottom_value:,.2f} to {top_value:,.2f}, showing which products need attention or improvement."
                    else:
                        return f"Here are your top {n} performing products by {column}. The top performer has {top_value:,.2f} in {column}, while the {n}th best has {bottom_value:,.2f}. These are your revenue drivers."
                
                elif 'revenue' in command_lower or 'sales' in command_lower:
                    if ascending:
                        return f"Here are the {n} items with the lowest {column}. The range is from {bottom_value:,.2f} to {top_value:,.2f}, highlighting areas that need improvement."
                    else:
                        return f"Here are your top {n} revenue generators by {column}. Your best performer generated {top_value:,.2f}, while the {n}th best generated {bottom_value:,.2f}. These represent your strongest revenue sources."
                
                else:
                    direction = "lowest" if ascending else "highest"
                    return f"I've found the {n} items with the {direction} {column} values. The range is from {bottom_value:,.2f} to {top_value:,.2f}, giving you a clear view of the {direction} performing items."
        
        elif operation_type == 'group_aggregate':
            group_cols = operation_params.get('group_columns', [])
            agg_dict = operation_params.get('agg_dict', {})
            
            if not data_results.empty and group_cols:
                # Get some actual values from the grouped data
                first_group = data_results.iloc[0][group_cols[0]] if group_cols[0] in data_results.columns else "category"
                total_groups = len(data_results)
                
                if 'region' in command_lower:
                    return f"I've grouped your data by {', '.join(group_cols)} and found {total_groups} different regions. This shows the performance breakdown across your markets, with '{first_group}' being one of the regions analyzed."
                
                elif 'quarter' in command_lower or 'time' in command_lower:
                    return f"I've grouped your data by {', '.join(group_cols)} and found {total_groups} time periods. This reveals seasonal patterns and trends, starting with '{first_group}' as one of the periods analyzed."
                
                elif 'product' in command_lower:
                    return f"I've grouped your data by {', '.join(group_cols)} and found {total_groups} product categories. This shows performance by product line, including '{first_group}' as one of the categories analyzed."
                
                else:
                    return f"I've grouped your data by {', '.join(group_cols)} and found {total_groups} different groups. This reveals patterns in your data, with '{first_group}' being one of the groups analyzed."
        
        elif operation_type == 'filter':
            column = operation_params.get('column', 'data')
            operator = operation_params.get('operator', 'equals')
            value = operation_params.get('value', 'criteria')
            filtered_count = len(data_results)
            
            if 'region' in command_lower:
                return f"I've filtered your data to show only {column} = {value}. This returned {filtered_count} records, focusing your analysis on this specific region to understand its unique characteristics."
            
            elif 'date' in command_lower or 'time' in command_lower:
                return f"I've filtered your data to show only records where {column} {operator} {value}. This returned {filtered_count} records, narrowing your view to this specific time period for focused analysis."
            
            else:
                return f"I've filtered your data to show only items where {column} {operator} {value}. This returned {filtered_count} records, giving you a focused view of this specific subset."
        
        elif operation_type == 'sort':
            columns = operation_params.get('columns', ['value'])
            ascending = operation_params.get('ascending', [False])[0]
            direction = "ascending" if ascending else "descending"
            sorted_count = len(data_results)
            
            if 'revenue' in command_lower or 'sales' in command_lower:
                return f"I've sorted your {sorted_count} records by {', '.join(columns)} in {direction} order. This shows your {'highest' if not ascending else 'lowest'} revenue items first, helping you identify your top performers."
            
            elif 'date' in command_lower or 'time' in command_lower:
                return f"I've sorted your {sorted_count} records by {', '.join(columns)} in {direction} order. This organizes your data chronologically, making it easier to see trends and patterns over time."
            
            else:
                return f"I've sorted your {sorted_count} records by {', '.join(columns)} in {direction} order. This organizes your data in a logical sequence for better analysis."
        
        # Return original explanation if no enhancement possible
        return original_explanation
    
    def _analyze_data_results(self, data_results: pd.DataFrame, operation_type: str, operation_params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the actual data results to provide context"""
        if data_results.empty:
            return {}
        
        analysis = {
            'row_count': len(data_results),
            'column_count': len(data_results.columns),
            'numeric_columns': data_results.select_dtypes(include=['number']).columns.tolist(),
            'categorical_columns': data_results.select_dtypes(include=['object']).columns.tolist()
        }
        
        # Add specific analysis based on operation type
        if operation_type == 'top_n':
            sort_column = operation_params.get('sort_column')
            if sort_column and sort_column in data_results.columns:
                analysis['min_value'] = data_results[sort_column].min()
                analysis['max_value'] = data_results[sort_column].max()
                analysis['avg_value'] = data_results[sort_column].mean()
        
        return analysis
    
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
        """Generate intelligent fallback suggestions based on data context"""
        suggestions = []
        
        # Get available columns
        numeric_cols = self.data_info.get('numeric_columns', [])
        categorical_cols = self.data_info.get('categorical_columns', [])
        all_columns = self.data_info.get('columns', [])
        
        # Business intelligence suggestions based on common patterns
        if numeric_cols:
            # Find revenue-related columns
            revenue_cols = [col for col in numeric_cols if any(term in col.lower() for term in ['revenue', 'sales', 'amount', 'value', 'price'])]
            if revenue_cols:
                suggestions.append({
                    "type": "command",
                    "description": f"Show top 10 by {revenue_cols[0]}",
                    "operation": {"command": f"top 10 by {revenue_cols[0]}"}
                })
            else:
                suggestions.append({
                    "type": "command", 
                    "description": f"Show top 10 by {numeric_cols[0]}",
                    "operation": {"command": f"top 10 by {numeric_cols[0]}"}
                })
        
        if categorical_cols:
            # Find region/geography columns
            region_cols = [col for col in categorical_cols if any(term in col.lower() for term in ['region', 'country', 'state', 'area', 'location'])]
            if region_cols:
                suggestions.append({
                    "type": "command",
                    "description": f"Group by {region_cols[0]} and sum revenue",
                    "operation": {"command": f"group by {region_cols[0]} and sum revenue"}
                })
            else:
                suggestions.append({
                    "type": "command",
                    "description": f"Group by {categorical_cols[0]}",
                    "operation": {"command": f"group by {categorical_cols[0]}"}
                })
        
        # Time-based analysis if date columns exist
        date_cols = self.data_info.get('date_columns', [])
        if date_cols and numeric_cols:
            suggestions.append({
                "type": "command",
                "description": f"Show revenue trend over time",
                "operation": {"command": f"group by {date_cols[0]} and sum revenue"}
            })
        
        # Product analysis if product columns exist
        product_cols = [col for col in categorical_cols if any(term in col.lower() for term in ['product', 'item', 'sku', 'category'])]
        if product_cols and numeric_cols:
            suggestions.append({
                "type": "command",
                "description": f"Show top products by revenue",
                "operation": {"command": f"top 5 products by revenue"}
            })
        
        # Chart visualization suggestions
        if numeric_cols and categorical_cols:
            suggestions.append({
                "type": "command",
                "description": f"Create a bar chart showing {numeric_cols[0]} by {categorical_cols[0]}",
                "operation": {"command": f"group by {categorical_cols[0]} and show chart"}
            })
        
        # If we don't have enough suggestions, add generic ones
        if len(suggestions) < 3:
            if numeric_cols:
                suggestions.append({
                    "type": "command",
                    "description": f"Sort by {numeric_cols[0]} descending",
                    "operation": {"command": f"sort by {numeric_cols[0]} descending"}
                })
        
        if len(suggestions) < 3 and categorical_cols:
            suggestions.append({
                "type": "command",
                "description": f"Filter by {categorical_cols[0]}",
                "operation": {"command": f"show all {categorical_cols[0]} values"}
            })
        
        return suggestions[:3]  # Return maximum 3 suggestions
    
    def suggest_chart_config(self, operation_type: str, operation_params: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Use LLM to suggest optimal chart configuration based on operation and data"""
        try:
            # Prepare context about the data and operation
            data_context = self._prepare_chart_context(df, operation_type, operation_params)
            
            # Create prompt for chart configuration
            chart_prompt = f"""You are a data visualization expert. Based on the operation and data, suggest the optimal chart configuration.

## OPERATION DETAILS:
- Type: {operation_type}
- Parameters: {operation_params}

## DATA CONTEXT:
{data_context}

## CHART CONFIGURATION REQUIREMENTS:
- Choose the best chart type from: bar, line, scatter, pie, histogram, box
- Select the most appropriate x-axis column (usually categorical or identifier)
- Select the most appropriate y-axis column (usually numeric/metric)
- Optionally suggest a color column for grouping
- Create a meaningful title

## RESPONSE FORMAT:
Return ONLY a JSON object with:
- "chart_type": string (one of the chart types above)
- "x_col": string (column name for x-axis)
- "y_col": string (column name for y-axis) 
- "color_col": string or null (column name for color grouping, if applicable)
- "title": string (descriptive chart title)

Focus on creating the most meaningful and informative visualization for this specific operation and data."""

            # Call OpenAI API (updated for v1.0+)
            from openai import OpenAI
            client = OpenAI()
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data visualization expert specializing in creating optimal chart configurations for business data analysis."},
                    {"role": "user", "content": chart_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            chart_config = json.loads(ai_response)
            
            # Validate the configuration
            if self._validate_chart_config(chart_config, df):
                return chart_config
            else:
                return self._get_fallback_chart_config(operation_type, df)
                
        except Exception as e:
            print(f"Chart configuration error: {e}")
            return self._get_fallback_chart_config(operation_type, df)
    
    def _prepare_chart_context(self, df: pd.DataFrame, operation_type: str, operation_params: Dict[str, Any]) -> str:
        """Prepare context about data for chart configuration"""
        context_parts = []
        
        # Basic data info
        context_parts.append(f"Dataset has {len(df)} rows and {len(df.columns)} columns.")
        context_parts.append(f"Columns: {', '.join(df.columns.tolist())}")
        
        # Data types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if numeric_cols:
            context_parts.append(f"Numeric columns: {', '.join(numeric_cols)}")
        if categorical_cols:
            context_parts.append(f"Categorical columns: {', '.join(categorical_cols)}")
        
        # Sample data
        if not df.empty:
            context_parts.append(f"Sample data (first 3 rows):")
            context_parts.append(df.head(3).to_string())
        
        # Operation-specific context
        if operation_type == 'top_n':
            sort_column = operation_params.get('sort_column', 'unknown')
            n = operation_params.get('n', 5)
            context_parts.append(f"This is a TOP {n} analysis sorted by '{sort_column}' - we want to show the top performers.")
        elif operation_type == 'group_aggregate':
            group_cols = operation_params.get('group_columns', [])
            context_parts.append(f"This is a GROUP BY analysis grouping by {group_cols} - we want to show aggregated values by groups.")
        elif operation_type == 'pivot':
            context_parts.append("This is a PIVOT analysis - we want to show cross-tabulated data.")
        
        return "\n".join(context_parts)
    
    def _validate_chart_config(self, config: Dict[str, Any], df: pd.DataFrame) -> bool:
        """Validate that the chart configuration is valid for the data"""
        required_keys = ['chart_type', 'x_col', 'y_col', 'title']
        
        # Check required keys
        if not all(key in config for key in required_keys):
            return False
        
        # Check if columns exist
        if config['x_col'] not in df.columns or config['y_col'] not in df.columns:
            return False
        
        # Check chart type
        valid_chart_types = ['bar', 'line', 'scatter', 'pie', 'histogram', 'box']
        if config['chart_type'] not in valid_chart_types:
            return False
        
        # Check color column if provided
        if config.get('color_col') and config['color_col'] not in df.columns:
            return False
        
        return True
    
    def _get_fallback_chart_config(self, operation_type: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Get fallback chart configuration when LLM fails"""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Default configuration
        config = {
            "chart_type": "bar",
            "x_col": categorical_cols[0] if categorical_cols else df.columns[0],
            "y_col": numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0],
            "color_col": None,
            "title": f"{operation_type.replace('_', ' ').title()} Analysis"
        }
        
        # Operation-specific adjustments
        if operation_type == 'top_n' and len(df) > 0:
            # For top_n, try to use a meaningful identifier column
            id_cols = [col for col in categorical_cols if any(term in col.lower() for term in ['name', 'id', 'sku', 'product', 'item'])]
            if id_cols:
                config['x_col'] = id_cols[0]
        
        return config
    
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
