"""
Script to create the 'data/' directory for the project.
This satisfies task T001b: Create `data/` directory using `mkdir -p data`.
"""
import os
from pathlib import Path

def main():
    """Create the data directory if it does not exist."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {data_dir}")
    else:
        print(f"Directory already exists: {data_dir}")
    
    # Ensure it's writable and list contents (or lack thereof)
    try:
        files = list(data_dir.iterdir())
        print(f"Contents of {data_dir}: {files}")
    except PermissionError:
        print(f"Warning: Cannot list contents of {data_dir} due to permissions.")

if __name__ == "__main__":
    main()
