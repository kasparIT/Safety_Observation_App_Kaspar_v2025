import os
import pyodbc
from dotenv import load_dotenv
from contextlib import contextmanager
from flask import g
import time

# Load environment variables from .env
load_dotenv()

# Get Azure SQL credentials from .env
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DRIVER = os.getenv("DB_DRIVER")
DB_PORT = os.getenv("DB_PORT", 1433)

# Connection pool
connection_pool = None
max_pool_size = 5
current_connections = 0

def init_db_pool():
    """Initialize the database connection pool."""
    global connection_pool
    if connection_pool is None:
        connection_pool = []
        print("✅ Database connection pool initialized")

def get_connection_string():
    """Return the connection string for Azure SQL."""
    return (f"DRIVER={DB_DRIVER};"
            f"SERVER=tcp:{DB_SERVER},{DB_PORT};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USERNAME};"
            f"PWD={DB_PASSWORD};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;")

@contextmanager
def get_db_connection():
    """Get a database connection from the pool or create a new one."""
    global connection_pool, current_connections
    
    conn = None
    new_connection = False
    
    # Try to get a connection from the pool
    if connection_pool and len(connection_pool) > 0:
        try:
            conn = connection_pool.pop()
            # Check if connection is still valid
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        except Exception:
            # Connection is no longer valid, close it
            try:
                conn.close()
            except Exception:
                pass
            conn = None
    
    # If no connection from pool, create a new one
    if conn is None:
        try:
            start_time = time.time()
            conn = pyodbc.connect(get_connection_string())
            elapsed = time.time() - start_time
            print(f"✅ New DB connection created in {elapsed:.2f}s (current: {current_connections+1})")
            current_connections += 1
            new_connection = True
        except Exception as e:
            print(f"❌ Database Connection Failed: {e}")
            yield None
            return
    
    try:
        # Return the connection for use
        yield conn
        
        # Return connection to pool if it's still valid
        if conn and max_pool_size > len(connection_pool):
            try:
                # Check connection is still good before returning to pool
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                connection_pool.append(conn)
                conn = None  # Don't close the connection below
            except Exception:
                # Connection had an issue, don't return it to pool
                pass
    finally:
        # Close the connection if it wasn't returned to the pool
        if conn:
            try:
                conn.close()
                if new_connection:
                    current_connections -= 1
            except Exception:
                pass

def get_companies():
    """Get the list of companies from the database with caching."""
    # Check if we have companies cached in the application context
    if hasattr(g, 'companies_cache'):
        return g.companies_cache
    
    companies = []
    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT DISTINCT Company_Name FROM dbo.Paylocity_Employee_Data WHERE Company_Name IS NOT NULL")
                fetched_companies = [row[0] for row in cursor.fetchall()]
                
                # We can't import COMPANY_NAME_MAPPING directly to avoid circular imports
                # So we'll build a simple mapping here
                company_mapping = {
                    "HFA": "HFA - Kaspar Outdoors",
                    "KCI": "KCI - Kaspar Companies Inc.",
                    "KPI": "KPI - Kaspar Properties",
                    "TA": "TA - Texas Ammunition",
                    "TBE": "TBE - Bedrock Truck Beds",
                    "TPM": "TPM - Texas Precious Metals",
                    "TRK": "TRK - Kaspar Trucking",
                    "WHL": "WHL - Circle Y Saddles & Precision Saddle Tree"
                }
                
                companies = [(abbr, company_mapping.get(abbr, abbr)) for abbr in fetched_companies]
                
                # Cache the results
                g.companies_cache = companies
            except Exception as e:
                print(f"❌ Error fetching companies: {e}")
            finally:
                cursor.close()
    
    return companies