"""
Script to initialize the metadata registry database.
Usage: python code/utils/setup_db.py
"""
from utils.db_schema import init_db
import sys
from pathlib import Path

def main():
    # Ensure we are running from project root or handle relative paths correctly
    # The db_schema module handles the path resolution to data/metadata_registry.db
    try:
        print("Initializing metadata registry database...")
        conn = init_db()
        print(f"Database initialized successfully at {conn.execute('PRAGMA database_list;').fetchone()[2]}")
        
        # Verify tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables created: {tables}")
        
        conn.close()
        print("Setup complete.")
    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
