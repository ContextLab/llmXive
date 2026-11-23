from utils.db_schema import init_db
import sys
from pathlib import Path

def main() -> None:
    """Initialize the database schema."""
    try:
        conn = init_db()
        print(f"Database initialized at {Path(__file__).resolve().parents[2] / 'data' / 'registry.db'}")
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
