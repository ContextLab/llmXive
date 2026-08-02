from utils.db_schema import init_db
import sys
from pathlib import Path

def main() -> None:
    """
    Entry point for initializing the SQLite metadata registry.
    Creates the database file and schema defined in db_schema.py.
    """
    print("Initializing metadata registry database...")
    try:
        init_db()
        print("Database initialized successfully at data/metadata_registry.db")
    except Exception as e:
        print(f"Failed to initialize database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
