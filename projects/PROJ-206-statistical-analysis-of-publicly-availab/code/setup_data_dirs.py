import os
import sys
from pathlib import Path

def main():
    """
    T001c: Create the `data/` directory at the project root.
    
    This script ensures the existence of the data directory required for 
    storing raw and processed datasets. It creates the directory if it 
    does not exist and prints a confirmation message.
    """
    # Determine project root (assuming this script is at code/setup_data_dirs.py)
    # We go up two levels from code/ to reach the root, or check if we are in code/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    data_dir = project_root / "data"
    
    if data_dir.exists():
        print(f"Directory {data_dir} already exists.")
        return 0
    
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created directory: {data_dir}")
        
        # Create standard subdirectories to ensure the structure is initialized
        # as per T004 (though T004 is a separate task, we ensure the root exists here)
        (data_dir / "raw").mkdir(exist_ok=True)
        (data_dir / "processed").mkdir(exist_ok=True)
        print(f"Created standard subdirectories: raw/, processed/")
        
        return 0
    except PermissionError:
        print(f"Error: Permission denied when trying to create {data_dir}")
        return 1
    except Exception as e:
        print(f"Error creating directory {data_dir}: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
