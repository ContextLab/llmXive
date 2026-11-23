import os
import sys
from pathlib import Path

def main():
    """
    Creates the required data directory structure for the llmXive project.
    Specifically creates 'data/raw' as per task T001h, and ensures the
    parent 'data' directory exists.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"

    # Ensure parent directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the specific target directory
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created directory: {raw_dir}")
    
    # Verify creation
    if raw_dir.exists() and raw_dir.is_dir():
        print(f"Success: {raw_dir} is ready.")
        return 0
    else:
        print(f"Error: Failed to create {raw_dir}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
