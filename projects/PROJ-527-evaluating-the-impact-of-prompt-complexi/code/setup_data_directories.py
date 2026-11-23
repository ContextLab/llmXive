import os
from pathlib import Path

def create_data_directories():
    """
    Create the data directory structure.
    Helper function called by setup_project_structure.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
    ]
    
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
    
    return True

def main():
    """Entry point for data directory creation."""
    create_data_directories()
    print("Data directories created successfully.")

if __name__ == "__main__":
    main()
