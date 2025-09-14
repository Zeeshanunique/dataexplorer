import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

class DatabaseManager:
    def __init__(self, db_path: str = "dataexplorer.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_info TEXT,
                    current_data TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_command TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    operation_type TEXT,
                    operation_params TEXT,
                    confidence REAL,
                    suggestions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # Data snapshots table for storing data at different points
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    data_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            conn.commit()
    
    def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (id, created_at, updated_at)
                VALUES (?, ?, ?)
            """, (session_id, datetime.now(), datetime.now()))
            conn.commit()
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, created_at, updated_at, data_info, current_data, is_active
                FROM sessions WHERE id = ? AND is_active = 1
            """, (session_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'created_at': row[1],
                    'updated_at': row[2],
                    'data_info': json.loads(row[3]) if row[3] else None,
                    'current_data': json.loads(row[4]) if row[4] else None,
                    'is_active': bool(row[5])
                }
        return None
    
    def update_session_data(self, session_id: str, data_info: Dict = None, current_data: List[Dict] = None):
        """Update session with new data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update session
            cursor.execute("""
                UPDATE sessions 
                SET updated_at = ?, data_info = ?, current_data = ?
                WHERE id = ?
            """, (
                datetime.now(),
                json.dumps(data_info) if data_info else None,
                json.dumps(current_data) if current_data else None,
                session_id
            ))
            
            # Store data snapshot if current_data is provided
            if current_data:
                cursor.execute("""
                    INSERT INTO data_snapshots (session_id, data, data_info)
                    VALUES (?, ?, ?)
                """, (
                    session_id,
                    json.dumps(current_data),
                    json.dumps(data_info) if data_info else None
                ))
            
            conn.commit()
    
    def add_conversation(self, session_id: str, user_command: str, ai_response: str, 
                        operation_type: str = None, operation_params: Dict = None, 
                        confidence: float = None, suggestions: List[Dict] = None):
        """Add a conversation entry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations 
                (session_id, user_command, ai_response, operation_type, operation_params, confidence, suggestions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_command,
                ai_response,
                operation_type,
                json.dumps(operation_params) if operation_params else None,
                confidence,
                json.dumps(suggestions) if suggestions else None
            ))
            conn.commit()
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_command, ai_response, operation_type, operation_params, 
                       confidence, suggestions, created_at
                FROM conversations 
                WHERE session_id = ? 
                ORDER BY created_at ASC
            """, (session_id,))
            
            rows = cursor.fetchall()
            conversations = []
            for row in rows:
                conversations.append({
                    'user_command': row[0],
                    'ai_response': row[1],
                    'operation_type': row[2],
                    'operation_params': json.loads(row[3]) if row[3] else None,
                    'confidence': row[4],
                    'suggestions': json.loads(row[5]) if row[5] else None,
                    'created_at': row[6]
                })
            return conversations
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions for sidebar display"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.created_at, s.updated_at, s.data_info,
                       COUNT(c.id) as conversation_count
                FROM sessions s
                LEFT JOIN conversations c ON s.id = c.session_id
                WHERE s.is_active = 1
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            sessions = []
            for row in rows:
                sessions.append({
                    'id': row[0],
                    'created_at': row[1],
                    'updated_at': row[2],
                    'data_info': json.loads(row[3]) if row[3] else None,
                    'conversation_count': row[4]
                })
            return sessions
    
    def deactivate_session(self, session_id: str):
        """Deactivate a session (soft delete)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET is_active = 0, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), session_id))
            conn.commit()
    
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up old inactive sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM sessions 
                WHERE is_active = 0 AND updated_at < datetime('now', '-{} days')
            """.format(days))
            conn.commit()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total sessions
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
            active_sessions = cursor.fetchone()[0]
            
            # Total conversations
            cursor.execute("SELECT COUNT(*) FROM conversations")
            total_conversations = cursor.fetchone()[0]
            
            # Database size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'active_sessions': active_sessions,
                'total_conversations': total_conversations,
                'database_size_mb': round(db_size / (1024 * 1024), 2)
            }

# Global database instance
db_manager = DatabaseManager()
