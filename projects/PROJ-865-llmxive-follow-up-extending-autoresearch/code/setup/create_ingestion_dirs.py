import os
import sys
from pathlib import Path

def main():
    """
    Task T001g: Create directory `code/01_data_ingestion/` at repository root.
    
    This script ensures the data ingestion directory exists.
    It creates the directory if it does not exist and exits with status 0 on success.
    """
    project_root = Path.cwd()
    target_dir = project_root / "code" / "01_data_ingestion"
    
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully ensured directory exists: {target_dir}")
        return 0
    except OSError as e:
        print(f"Error creating directory {target_dir}: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())