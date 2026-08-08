import os
import sys
from pathlib import Path

def create_raw_data_directory():
    """
    Creates the directory structure for raw downloaded data.
    Specifically creates: projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/data/raw/
    
    Returns:
        Path: The path to the created raw data directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    project_path = project_root / project_name
    
    data_dir = project_path / "data"
    raw_dir = data_dir / "raw"
    
    # Ensure parent directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the raw directory
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Raw data directory created at: {raw_dir}")
    return raw_dir

def main():
    """Entry point for the script."""
    try:
        raw_dir = create_raw_data_directory()
        if raw_dir.exists() and raw_dir.is_dir():
            print(f"Success: Directory {raw_dir} is ready.")
            sys.exit(0)
        else:
            print(f"Error: Failed to create directory {raw_dir}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()