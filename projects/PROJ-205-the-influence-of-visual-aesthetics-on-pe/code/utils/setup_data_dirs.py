import os
from pathlib import Path

def main():
    """
    Creates the required data directory structure for the project.
    Specifically creates 'data/raw/' and 'data/processed/'.
    
    This script ensures that the storage locations for raw survey submissions
    and processed analysis results exist before data collection or analysis begins.
    """
    # Determine the project root based on this file's location
    # Assuming this file is at code/utils/setup_data_dirs.py
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent.parent
    
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    # Create directories if they do not exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a .gitkeep in each to ensure they are tracked by git
    # (though git doesn't track empty directories)
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()
    
    print(f"Data directory structure created at: {data_root}")
    print(f"  - Raw data: {raw_dir}")
    print(f"  - Processed data: {processed_dir}")

if __name__ == "__main__":
    main()