import os
from pathlib import Path

def main():
    """
    Create the required data directory structure for the project.
    
    Creates:
    - data/raw/
    - data/processed/
    - output/
    
    These directories are essential for storing raw downloaded data,
    processed intermediate results, and final outputs.
    """
    # Define the project root (parent of code/)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the directories to create
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "output",
    ]
    
    # Create directories if they don't exist
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()