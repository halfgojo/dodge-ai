import os
import sqlite3
import pandas as pd
import json

DB_PATH = "sqlite.db"
DATA_DIR = "sap-o2c-data"

def init_db():
    if os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} already exists. Skipping initialization.")
        return
        
    print("Initializing SQLite database from JSONL files...")
    conn = sqlite3.connect(DB_PATH)
    
    for table_name in os.listdir(DATA_DIR):
        table_dir = os.path.join(DATA_DIR, table_name)
        if not os.path.isdir(table_dir):
            continue
            
        dfs = []
        for file in os.listdir(table_dir):
            if file.endswith('.jsonl'):
                file_path = os.path.join(table_dir, file)
                try:
                    df = pd.read_json(file_path, lines=True)
                    for col in df.columns:
                        df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
                    dfs.append(df)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            print(f"Writing {len(combined_df)} rows to table {table_name}")
            combined_df.to_sql(table_name, conn, if_exists='replace', index=False)
            
    conn.close()
    print("Database initialization complete.")

def run_query(query: str):
    """Executes a SELECT query and returns results as a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    try:
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")
            
        df = pd.read_sql_query(query, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_schema():
    """Returns a dictionary mapping table names to their a list of column names."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [row[1] for row in cursor.fetchall()]
        schema[table] = columns
        
    conn.close()
    return schema

if __name__ == "__main__":
    init_db()
