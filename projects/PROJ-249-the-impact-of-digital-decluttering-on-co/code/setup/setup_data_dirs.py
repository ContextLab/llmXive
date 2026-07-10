import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Creates the required data directory structure for the project.
    
    Directories created:
    - data/raw: For raw, unprocessed data files
    - data/processed: For cleaned and transformed data
    - data/compliance: For compliance logs and validation records
    
    This function ensures all directories exist, creating them if necessary.
    """
    # Define the project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    # Define data directories relative to project root
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    compliance_dir = data_root / "compliance"
    
    directories = [
        data_root,
        raw_dir,
        processed_dir,
        compliance_dir
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Data directory setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    setup_data_directories()
