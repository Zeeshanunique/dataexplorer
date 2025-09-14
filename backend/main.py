"""
FastAPI backend for Data Explorer with Natural Commands
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import json
import io
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime

from operations import DataOperations
from conversational_ai import ConversationalAI
from chart_generator import ChartGenerator
from database import db_manager

app = FastAPI(title="Data Explorer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database-backed session management
class SessionManager:
    def __init__(self):
        self.chart_generator = ChartGenerator()
        self._sessions = {}  # In-memory session cache
    
    def create_session(self) -> str:
        """Create a new session using database"""
        return db_manager.create_session()
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session from database and cache"""
        # Check in-memory cache first
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # Get from database
        session_data = db_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add runtime components
        data_ops = None
        conversational_ai = None
        
        # Recreate data_ops and conversational_ai if data is available
        if session_data.get('data_info') and session_data.get('current_data'):
            try:
                # Convert current_data back to DataFrame
                df = pd.DataFrame(session_data['current_data'])
                data_ops = DataOperations(df)
                conversational_ai = ConversationalAI(session_data['data_info'])
            except Exception as e:
                print(f"Warning: Failed to recreate data objects: {e}")
        
        session_data.update({
            "data_ops": data_ops,
            "conversational_ai": conversational_ai,
            "chart_generator": self.chart_generator,
            "conversation_history": db_manager.get_conversation_history(session_id),
            "operation_history": [],
            "current_view": session_data.get('current_data')
        })
        
        # Cache the session
        self._sessions[session_id] = session_data
        return session_data
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session in database and cache"""
        session_data = db_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update database with new data
        data_info = updates.get('data_info')
        current_data = updates.get('current_data')
        
        if data_info or current_data:
            db_manager.update_session_data(session_id, data_info, current_data)
        
        # Update in-memory cache
        if session_id in self._sessions:
            # Update the cached session with new data
            if 'data_ops' in updates:
                self._sessions[session_id]['data_ops'] = updates['data_ops']
            if 'conversational_ai' in updates:
                self._sessions[session_id]['conversational_ai'] = updates['conversational_ai']
            if 'current_view' in updates:
                self._sessions[session_id]['current_view'] = updates['current_view']
            if 'conversation_history' in updates:
                self._sessions[session_id]['conversation_history'] = updates['conversation_history']
            if 'operation_history' in updates:
                self._sessions[session_id]['operation_history'] = updates['operation_history']
        
        # Store conversation if provided
        if 'conversation_history' in updates:
            conversation = updates['conversation_history'][-1] if updates['conversation_history'] else None
            if conversation:
                db_manager.add_conversation(
                    session_id=session_id,
                    user_command=conversation.get('user_command', ''),
                    ai_response=conversation.get('ai_response', ''),
                    operation_type=conversation.get('operation_type'),
                    operation_params=conversation.get('operation_params'),
                    confidence=conversation.get('confidence'),
                    suggestions=conversation.get('suggestions')
                )

session_manager = SessionManager()

@app.get("/")
async def root():
    return {"message": "Data Explorer API", "version": "1.0.0"}

@app.post("/sessions")
async def create_session():
    """Create a new session"""
    session_id = session_manager.create_session()
    return {"session_id": session_id}

@app.post("/sessions/{session_id}/upload")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    """Upload and process a data file"""
    try:
        # Get session
        session = session_manager.get_session(session_id)
        
        # Read file based on extension
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        elif file.filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Initialize data operations and AI
        data_ops = DataOperations(df)
        conversational_ai = ConversationalAI(data_ops.get_data_info())
        
        # Get data info
        data_info = data_ops.get_data_info()
        
        # Update session
        session_manager.update_session(session_id, {
            "data_ops": data_ops,
            "conversational_ai": conversational_ai,
            "current_view": df.to_dict('records'),
            "conversation_history": [],
            "operation_history": [],
            "data_info": data_info,
            "current_data": df.to_dict('records')
        })
        
        return {
            "message": "File uploaded successfully",
            "shape": df.shape,
            "columns": list(df.columns),
            "data_types": df.dtypes.astype(str).to_dict(),
            "sample_data": df.head(5).to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/sessions/{session_id}/data-info")
async def get_data_info(session_id: str):
    """Get information about the current dataset"""
    session = session_manager.get_session(session_id)
    
    if not session["data_ops"]:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    data_info = session["data_ops"].get_data_info()
    return data_info

@app.post("/sessions/{session_id}/command")
async def process_command(session_id: str, command_data: Dict[str, str]):
    """Process a natural language command"""
    session = session_manager.get_session(session_id)
    
    if not session["conversational_ai"]:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    command = command_data.get("command", "")
    if not command:
        raise HTTPException(status_code=400, detail="Command is required")
    
    try:
        # Process command with conversational AI
        current_df = pd.DataFrame(session["current_view"]) if session["current_view"] else None
        result = session["conversational_ai"].process_conversational_command(command, current_df)
        
        # Execute operation if valid
        if result.get("operation_type"):
            operation_params = result["operation_params"]
            operation_type = result["operation_type"].lower()
            
            # Execute the operation
            if operation_type == 'top_n':
                df_result = session["data_ops"].get_top_n(**operation_params)
            elif operation_type == 'filter':
                df_result = session["data_ops"].filter_data(**operation_params)
            elif operation_type == 'group_aggregate':
                df_result = session["data_ops"].group_and_aggregate(**operation_params)
            elif operation_type == 'sort':
                df_result = session["data_ops"].sort_data(**operation_params)
            elif operation_type == 'pivot':
                df_result = session["data_ops"].pivot_table(**operation_params)
            elif operation_type == 'correlation':
                df_result = session["data_ops"].correlation_analysis(**operation_params)
            else:
                df_result = session["data_ops"].df
            
            # Update the data_ops object with the new result for context persistence
            session["data_ops"].df = df_result
            
            # Generate multiple chart types for comprehensive visualization
            charts = {}
            if operation_type in ['top_n', 'group_aggregate', 'pivot'] and not df_result.empty:
                try:
                    # Use LLM to determine optimal chart configuration
                    chart_config = session["conversational_ai"].suggest_chart_config(
                        operation_type, operation_params, df_result
                    )
                    
                    # Generate multiple chart types
                    chart_types = ['bar', 'line', 'scatter', 'pie', 'histogram', 'box']
                    for chart_type in chart_types:
                        try:
                            chart = session["chart_generator"].generate_chart(
                                df_result,
                                chart_type=chart_type,
                                x_col=chart_config.get('x_col'),
                                y_col=chart_config.get('y_col'),
                                color_col=chart_config.get('color_col'),
                                title=f"{chart_config.get('title', f'{operation_type.replace('_', ' ').title()} Analysis')} - {chart_type.title()}"
                            )
                            charts[chart_type] = chart.to_json()
                        except Exception as chart_error:
                            print(f"Failed to generate {chart_type} chart: {chart_error}")
                            continue
                except Exception as e:
                    print(f"Chart generation failed: {e}")
                    charts = {}
            
            # Enhance explanation with actual data context
            enhanced_explanation = session["conversational_ai"].enhance_explanation_with_data_context(
                result.get('ai_explanation', result.get('explanation', '')),
                operation_type,
                operation_params,
                df_result,
                command
            )
            
            # Update session with new data
            current_data = df_result.to_dict('records')
            session_manager.update_session(session_id, {
                "current_data": current_data,
                "operation_history": session["data_ops"].operation_history,
                "conversation_history": session["conversation_history"] + [{
                    "user_command": command,
                    "ai_explanation": enhanced_explanation,
                    "operation_type": result.get('operation_type'),
                    "operation_params": operation_params,
                    "confidence": result.get('confidence'),
                    "suggestions": result.get('suggestions', [])
                }]
            })
            
            # Update the session's data_ops and conversational_ai for next query
            session["data_ops"] = session["data_ops"]  # Already updated above
            session["conversational_ai"] = ConversationalAI(session["data_ops"].get_data_info())
            
            return {
                "success": True,
                "operation_type": operation_type,
                "ai_explanation": enhanced_explanation,
                "data": df_result.to_dict('records'),
                "shape": df_result.shape,
                "suggestions": result.get('suggestions', []),
                "charts": charts
            }
        else:
            # Return suggestions for unclear commands
            return {
                "success": False,
                "explanation": result.get('ai_explanation', result.get('explanation', '')),
                "suggestions": result.get('suggestions', [])
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing command: {str(e)}")

@app.get("/sessions/{session_id}/data")
async def get_current_data(session_id: str, limit: int = 1000):
    """Get current data view"""
    session = session_manager.get_session(session_id)
    
    if not session["current_view"]:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    data = session["current_view"][:limit]  # Limit for performance
    return {
        "data": data,
        "total_rows": len(session["current_view"]),
        "displayed_rows": len(data)
    }

@app.post("/sessions/{session_id}/chart")
async def generate_chart(session_id: str, chart_config: Dict[str, Any]):
    """Generate a chart"""
    session = session_manager.get_session(session_id)
    
    if not session["current_view"]:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        df = pd.DataFrame(session["current_view"])
        chart_generator = session["chart_generator"]
        
        chart = chart_generator.generate_chart(
            df,
            chart_type=chart_config.get("type", "bar"),
            x_col=chart_config.get("x_col"),
            y_col=chart_config.get("y_col"),
            color_col=chart_config.get("color_col"),
            title=chart_config.get("title")
        )
        
        # Convert plotly chart to JSON
        chart_json = chart.to_json()
        
        return {"chart": chart_json}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.get("/sessions/{session_id}/export")
async def export_data(session_id: str, format: str = "csv"):
    """Export current data view"""
    session = session_manager.get_session(session_id)
    
    if not session["current_view"]:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        df = pd.DataFrame(session["current_view"])
        
        if format == "csv":
            csv_data = df.to_csv(index=False)
            return {"data": csv_data, "content_type": "text/csv"}
        elif format == "json":
            json_data = df.to_json(orient='records', indent=2)
            return {"data": json_data, "content_type": "application/json"}
        elif format == "excel":
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            excel_data = excel_buffer.getvalue()
            return {"data": excel_data, "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")

@app.get("/sessions/{session_id}/conversation")
async def get_conversation_history(session_id: str):
    """Get conversation history"""
    session = session_manager.get_session(session_id)
    return {"conversation": session["conversation_history"]}

@app.get("/sessions/recent")
async def get_recent_sessions(limit: int = 10):
    """Get recent sessions for sidebar display"""
    sessions = db_manager.get_recent_sessions(limit)
    return {"sessions": sessions}

@app.get("/sessions/stats")
async def get_session_stats():
    """Get database statistics"""
    stats = db_manager.get_session_stats()
    return stats

@app.post("/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset session to original data"""
    session = session_manager.get_session(session_id)
    
    if not session["data_ops"]:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    session["data_ops"].reset()
    session_manager.update_session(session_id, {
        "current_view": session["data_ops"].df.to_dict('records'),
        "operation_history": [],
        "conversation_history": []
    })
    
    return {"message": "Session reset to original data"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
