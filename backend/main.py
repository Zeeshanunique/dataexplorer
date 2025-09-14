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

app = FastAPI(title="Data Explorer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for sessions (in production, use Redis or database)
sessions = {}

class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "data_ops": None,
            "conversational_ai": None,
            "chart_generator": ChartGenerator(),
            "conversation_history": [],
            "operation_history": [],
            "current_view": None,
            "created_at": datetime.now()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)

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
        
        # Update session
        session_manager.update_session(session_id, {
            "data_ops": data_ops,
            "conversational_ai": conversational_ai,
            "current_view": df.to_dict('records'),
            "conversation_history": [],
            "operation_history": []
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
            operation_type = result["operation_type"]
            
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
            else:
                df_result = session["data_ops"].df
            
            # Update session
            session_manager.update_session(session_id, {
                "current_view": df_result.to_dict('records'),
                "operation_history": session["data_ops"].operation_history,
                "conversation_history": session["conversation_history"] + [{
                    "user": command,
                    "ai": result.get('ai_explanation', result.get('explanation', '')),
                    "operation": result.get('operation_type')
                }]
            })
            
            return {
                "success": True,
                "operation_type": operation_type,
                "ai_explanation": result.get('ai_explanation', result.get('explanation', '')),
                "data": df_result.to_dict('records'),
                "shape": df_result.shape,
                "suggestions": result.get('suggestions', [])
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
