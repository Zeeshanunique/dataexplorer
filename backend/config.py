"""
Configuration settings for the Data Explorer app
"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# App configuration
APP_TITLE = "Data Explorer with Natural Commands"
APP_DESCRIPTION = "Upload your data and explore it using natural language commands"

# Data processing limits
MAX_ROWS_DISPLAY = 1000
MAX_FILE_SIZE_MB = 50

# Chart configuration
DEFAULT_CHART_TYPE = "bar"
CHART_TYPES = ["bar", "line", "scatter", "pie", "histogram", "box"]

# Export formats
EXPORT_FORMATS = ["CSV", "Excel", "JSON"]
