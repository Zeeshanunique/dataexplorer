# Data Explorer with Natural Commands - Full Stack Architecture

A modern, full-stack data exploration application with natural language commands, built with Next.js frontend and Python FastAPI backend.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│   Next.js       │◄──────────────────►│   FastAPI       │
│   Frontend      │                    │   Backend       │
│                 │                    │                 │
│ • React UI      │                    │ • Data Ops      │
│ • TypeScript    │                    │ • AI Processing │
│ • Tailwind CSS  │                    │ • Chart Gen     │
│ • Plotly Charts │                    │ • File Upload   │
└─────────────────┘                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.8+
- npm or yarn

### 1. Start the Backend (Python FastAPI)
```bash
# Option 1: Use the startup script
./start_backend.sh

# Option 2: Manual setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The backend will be available at: `http://localhost:8000`

### 2. Start the Frontend (Next.js)
```bash
# Option 1: Use the startup script
./start_frontend.sh

# Option 2: Manual setup
cd frontend
npm install
npm run dev
```

The frontend will be available at: `http://localhost:3000`

## 📁 Project Structure

```
dataexplorer/
├── backend/                    # Python FastAPI Backend
│   ├── main.py                # FastAPI application
│   ├── operations.py          # Data operations library
│   ├── conversational_ai.py   # AI command processing
│   ├── chart_generator.py     # Chart generation
│   ├── config.py              # Configuration
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx       # Main page component
│   │   ├── components/        # React components
│   │   │   ├── FileUpload.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── CommandInterface.tsx
│   │   │   ├── ChartArea.tsx
│   │   │   ├── ConversationHistory.tsx
│   │   │   └── OperationExplanation.tsx
│   │   ├── context/
│   │   │   └── DataExplorerContext.tsx
│   │   └── config/
│   │       └── api.ts
│   ├── package.json
│   └── tailwind.config.js
│
├── start_backend.sh           # Backend startup script
├── start_frontend.sh          # Frontend startup script
└── README_NEW_ARCHITECTURE.md
```

## 🔧 Backend API Endpoints

### Session Management
- `POST /sessions` - Create a new session
- `GET /sessions/{session_id}/data-info` - Get dataset information
- `POST /sessions/{session_id}/reset` - Reset session to original data

### Data Operations
- `POST /sessions/{session_id}/upload` - Upload data file
- `GET /sessions/{session_id}/data` - Get current data view
- `POST /sessions/{session_id}/command` - Process natural language command

### Visualization & Export
- `POST /sessions/{session_id}/chart` - Generate chart
- `GET /sessions/{session_id}/export` - Export data (CSV/JSON/Excel)

### Conversation
- `GET /sessions/{session_id}/conversation` - Get conversation history

## 🎨 Frontend Features

### Core Components
- **FileUpload**: Drag & drop file upload with validation
- **DataTable**: Paginated data display with sorting
- **CommandInterface**: Natural language command input
- **ChartArea**: Interactive chart generation with Plotly
- **ConversationHistory**: Chat-like conversation display
- **OperationExplanation**: Clear operation descriptions

### Key Features
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live data updates and chart generation
- **Session Management**: Persistent sessions across page refreshes
- **Error Handling**: User-friendly error messages
- **Loading States**: Visual feedback during operations

## 🤖 AI Integration

### Conversational AI
- **OpenAI Integration**: Uses GPT-3.5-turbo for natural language processing
- **Fallback Mode**: Works without API key using pattern matching
- **Context Awareness**: Understands data structure and previous operations
- **Smart Suggestions**: Proactive recommendations based on data

### Supported Commands
- **Top N Queries**: "Show me the top 5 products by sales"
- **Grouping**: "Group by region and show total sales"
- **Filtering**: "Show only products with price > 1000"
- **Sorting**: "Sort by revenue descending"
- **Pivot Tables**: "Create a pivot table by region and quarter"

## 📊 Data Operations

### Supported File Formats
- **CSV**: Comma-separated values
- **Excel**: .xlsx and .xls files
- **JSON**: JSON data files

### Operations Library
- **Filter**: Equals, not equals, greater/less than, contains, starts/ends with
- **Sort**: Single or multiple columns, ascending/descending
- **Group & Aggregate**: Sum, count, average, min, max
- **Pivot Tables**: Cross-tabulation with custom aggregations
- **Top N**: Get best/worst performing items

## 🎯 Usage Examples

### 1. Upload and Explore Data
1. Open `http://localhost:3000`
2. Upload your CSV/Excel/JSON file
3. Ask questions like "What are the top selling products?"
4. View results in the data table and charts

### 2. Natural Language Commands
```
"Show me the top 5 products by revenue"
"Group by region and show total sales"
"Filter where price > 1000"
"Create a chart showing sales by quarter"
"Export this data as CSV"
```

### 3. Interactive Charts
- Configure chart type, X/Y axes, and color coding
- Auto-generate charts based on data structure
- Interactive Plotly charts with zoom, pan, and hover

## 🔧 Configuration

### Backend Configuration
Edit `backend/config.py`:
```python
OPENAI_API_KEY = "your_openai_api_key_here"
MAX_ROWS_DISPLAY = 1000
MAX_FILE_SIZE_MB = 50
```

### Frontend Configuration
Edit `frontend/src/config/api.ts`:
```typescript
export const API_BASE_URL = 'http://localhost:8000';
```

## 🚀 Deployment

### Backend Deployment
```bash
# Using uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000

# Using gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Start production server
npm start

# Or deploy to Vercel/Netlify
vercel deploy
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 📈 Performance

- **Backend**: Handles datasets up to 50MB efficiently
- **Frontend**: Optimized with React hooks and memoization
- **Charts**: Plotly.js for smooth, interactive visualizations
- **Pagination**: Large datasets displayed in manageable chunks

## 🔒 Security

- **CORS**: Configured for localhost development
- **File Validation**: Strict file type and size validation
- **Input Sanitization**: All user inputs are sanitized
- **Session Management**: Secure session handling

## 🛠️ Development

### Adding New Operations
1. Add operation method to `backend/operations.py`
2. Add API endpoint to `backend/main.py`
3. Add frontend component or update existing ones
4. Update TypeScript types if needed

### Adding New Chart Types
1. Add chart method to `backend/chart_generator.py`
2. Update chart configuration in `frontend/src/components/ChartArea.tsx`
3. Add new chart type to the dropdown

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🎉 Benefits of This Architecture

1. **Separation of Concerns**: Clean separation between frontend and backend
2. **Scalability**: Each service can be scaled independently
3. **Technology Choice**: Use the best tools for each layer
4. **Maintainability**: Easier to maintain and update individual components
5. **Team Collaboration**: Frontend and backend teams can work independently
6. **Deployment Flexibility**: Deploy services to different environments
7. **API Reusability**: Backend API can be used by other applications

---

**The new architecture provides a modern, scalable, and maintainable solution for data exploration with natural language commands!** 🚀
