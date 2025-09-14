# Data Explorer with Natural Commands - ChatGPT-like Interface

A modern, full-stack data exploration application with a ChatGPT-like conversational interface, built with Next.js frontend and Python FastAPI backend.

## 🎯 Overview

Data Explorer transforms data analysis into natural conversations. Simply upload your data and chat with an AI assistant that understands your questions and provides instant insights with beautiful visualizations.

## ✨ Key Features

### 🤖 **ChatGPT-like Interface**
- **Conversational UI**: Chat naturally with your data
- **Real-time Responses**: Instant AI-powered data analysis
- **Smart Suggestions**: Clickable suggestions for follow-up questions
- **Data Tables**: Beautiful tables showing results directly in chat
- **Session Management**: Persistent conversations across queries

### 📊 **Powerful Data Operations**
- **Natural Language Commands**: "Show me the top 5 products by sales"
- **Advanced Filtering**: "Filter where price > 1000"
- **Grouping & Aggregation**: "Group by region and sum revenue"
- **Sorting**: "Sort by revenue descending"
- **Pivot Tables**: "Create a pivot table by region and quarter"

### 📈 **Interactive Visualizations**
- **Auto-generated Charts**: Charts appear automatically with results
- **Multiple Chart Types**: Bar, line, scatter, pie charts
- **Interactive Plotly**: Zoom, pan, hover for detailed exploration
- **Responsive Design**: Works perfectly on desktop and mobile

### 🔧 **Enterprise-Ready**
- **Multiple File Formats**: CSV, Excel (.xlsx, .xls), JSON
- **Large Dataset Support**: Handles thousands of rows efficiently
- **Export Capabilities**: Download results as CSV
- **Error Handling**: Graceful error recovery with helpful messages
- **Session Recovery**: Automatic session management

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│   Next.js       │◄──────────────────►│   FastAPI       │
│   Frontend      │                    │   Backend       │
│                 │                    │                 │
│ • ChatGPT UI    │                    │ • Data Ops      │
│ • TypeScript    │                    │ • AI Processing │
│ • Tailwind CSS  │                    │ • Chart Gen     │
│ • Plotly Charts │                    │ • File Upload   │
└─────────────────┘                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.8+
- OpenAI API key (optional, has fallback mode)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd dataexplorer
```

### 2. Start the Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Backend runs at: `http://localhost:8000`

### 3. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:3000`

### 4. Configure OpenAI (Optional)
Create `backend/.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 📁 Project Structure

```
dataexplorer/
├── backend/                    # Python FastAPI Backend
│   ├── main.py                # FastAPI application & API endpoints
│   ├── operations.py          # Data operations library
│   ├── conversational_ai.py   # AI command processing
│   ├── chart_generator.py     # Chart generation
│   ├── config.py              # Configuration
│   ├── requirements.txt       # Python dependencies
│   └── venv/                  # Virtual environment
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx       # Main ChatGPT-like interface
│   │   ├── components/
│   │   │   ├── FileUpload.tsx # File upload component
│   │   │   └── ui/            # shadcn/ui components
│   │   ├── context/
│   │   │   └── DataExplorerContext.tsx # React context
│   │   └── lib/
│   │       └── utils.ts       # Utilities
│   ├── package.json
│   └── tailwind.config.js
│
├── Project5.csv               # Sample dataset
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🎨 User Experience

### 1. **Welcome Screen**
- Clean, modern interface with upload area
- Example prompts to get started
- Drag & drop file upload with validation

### 2. **Chat Interface**
- **User Messages**: Appear on the right with user avatar
- **AI Responses**: Appear on the left with bot avatar
- **Data Tables**: Results displayed in beautiful tables
- **Suggestions**: Clickable follow-up questions
- **Timestamps**: Track conversation history

### 3. **Data Visualization**
- **Automatic Charts**: Generated based on query results
- **Interactive Tables**: Sortable, paginated data display
- **Export Options**: Download results as CSV

## 🤖 AI Integration

### Conversational AI Features
- **OpenAI GPT-3.5-turbo**: Advanced natural language processing
- **Fallback Mode**: Works without API key using pattern matching
- **Context Awareness**: Understands data structure and previous operations
- **Smart Suggestions**: Proactive recommendations based on data

### Supported Commands
```
"Show me the top 5 products by sales"
"Group by region and show total revenue"
"Filter where price > 1000"
"Sort by revenue descending"
"Create a chart showing sales by quarter"
"What are the best performing products?"
"Show me products with high discount rates"
```

## 📊 Data Operations

### Supported File Formats
- **CSV**: Comma-separated values
- **Excel**: .xlsx and .xls files
- **JSON**: JSON data files

### Operations Library
- **Top N**: Get best/worst performing items
- **Filter**: Equals, not equals, greater/less than, contains
- **Sort**: Single or multiple columns, ascending/descending
- **Group & Aggregate**: Sum, count, average, min, max
- **Pivot Tables**: Cross-tabulation with custom aggregations

## 🎯 Usage Examples

### 1. **Basic Data Exploration**
1. Upload your CSV/Excel file
2. Ask: "What are the top 5 products by sales?"
3. View results in a beautiful table
4. Click suggestions for follow-up questions

### 2. **Advanced Analysis**
```
"Group by region and show total sales"
"Filter where price > 1000 and show top 10"
"Create a pivot table by quarter and region"
"Show me the correlation between price and sales"
```

### 3. **Interactive Exploration**
- Click on suggestions to explore further
- View data in tables with sorting and pagination
- Export results for further analysis
- Continue the conversation naturally

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
- **Session Management**: Efficient in-memory session storage

## 🔒 Security

- **CORS**: Configured for localhost development
- **File Validation**: Strict file type and size validation
- **Input Sanitization**: All user inputs are sanitized
- **Session Management**: Secure session handling
- **Error Handling**: Graceful error recovery

## 🛠️ Development

### Adding New Operations
1. Add operation method to `backend/operations.py`
2. Add API endpoint to `backend/main.py`
3. Update frontend context if needed
4. Test with natural language commands

### Adding New Chart Types
1. Add chart method to `backend/chart_generator.py`
2. Update chart configuration in frontend
3. Test with data visualization commands

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🎉 Key Benefits

1. **ChatGPT-like Experience**: Natural, conversational data analysis
2. **No Learning Curve**: Just ask questions in plain English
3. **Instant Insights**: Get answers immediately with visualizations
4. **Smart Suggestions**: AI suggests follow-up questions
5. **Beautiful UI**: Modern, responsive interface
6. **Enterprise Ready**: Handles large datasets efficiently
7. **Extensible**: Easy to add new operations and features

## 🔄 Session Management

- **Automatic Sessions**: Created when you upload data
- **Session Recovery**: Graceful handling of expired sessions
- **Error Messages**: Clear instructions when sessions expire
- **Data Persistence**: Upload data again to continue conversations

## 📊 Sample Data

The project includes `Project5.csv` with sample sales data:
- 6,199 rows of sales data
- 19 columns including date, region, product, revenue, etc.
- Perfect for testing and demonstration

---

**Transform your data analysis into natural conversations with Data Explorer!** 🚀

**Just upload your data and start chatting with your AI data assistant!** 💬📊