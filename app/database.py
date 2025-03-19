import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get Azure SQL credentials from .env
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DRIVER = os.getenv("DB_DRIVER")
DB_PORT = os.getenv("DB_PORT", 1433)

def get_db_connection():
    """Establishes and returns a database connection to Azure SQL."""
    try:
        conn = pyodbc.connect(
            f"DRIVER={DB_DRIVER};"
            f"SERVER=tcp:{DB_SERVER},{DB_PORT};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USERNAME};"
            f"PWD={DB_PASSWORD};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        print("✅ Connected to Azure SQL Database!")
        return conn
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")
        return None
