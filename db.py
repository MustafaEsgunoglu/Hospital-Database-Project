# db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_engine():
    server = os.getenv("MSSQL_SERVER")
    db = os.getenv("MSSQL_DB")
    driver = os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server")

    odbc = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={db};"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes;"
    )

    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={odbc}",
        future=True
    )
    return engine
