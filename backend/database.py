import os
import sqlite3
import pandas as pd
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sqlite.db")
DATA_DIR = os.path.join(BASE_DIR, "sap-o2c-data")

def init_db():
    if os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} already exists. Skipping initialization.")
        return
    
    if not os.path.exists(DATA_DIR):
        print(f"Data directory {DATA_DIR} not found. Please download and extract the dataset first.")
        return
        
    print("Initializing SQLite database from JSONL files...")
    conn = sqlite3.connect(DB_PATH)
    
    for table_name in sorted(os.listdir(DATA_DIR)):
        table_dir = os.path.join(DATA_DIR, table_name)
        if not os.path.isdir(table_dir):
            continue
            
        dfs = []
        for file in sorted(os.listdir(table_dir)):
            if file.endswith('.jsonl'):
                file_path = os.path.join(table_dir, file)
                try:
                    df = pd.read_json(file_path, lines=True)
                    for col in df.columns:
                        df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
                    dfs.append(df)
                except Exception as e:
                    print(f"  Error reading {file_path}: {e}")
                    
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            print(f"  {table_name}: {len(combined_df)} rows")
            combined_df.to_sql(table_name, conn, if_exists='replace', index=False)
            
    conn.close()
    print("Database initialization complete.")

def run_query(query: str):
    """Executes a read-only SELECT query and returns results as a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cleaned = query.strip()
        # Strip trailing semicolons for safety
        while cleaned.endswith(';'):
            cleaned = cleaned[:-1].strip()
        
        if not cleaned.upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")
        
        # Block dangerous patterns
        dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'ATTACH', 'DETACH']
        upper = cleaned.upper()
        for word in dangerous:
            if word in upper:
                raise ValueError(f"Query contains forbidden keyword: {word}")
            
        df = pd.read_sql_query(cleaned, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_schema():
    """Returns a dictionary mapping table names to a list of column names."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
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
    schema = get_schema()
    print(f"\nDatabase has {len(schema)} tables:")
    for table, cols in schema.items():
        print(f"  {table}: {len(cols)} columns")
