import os
from pathlib import Path

def create_project_directories():
    """
    Creates the required directory structure for the project:
    - data/raw
    - data/processed
    - results
    
    This script ensures the directories exist on disk as per task T001b.
    """
    # Define the base project root relative to this script's location
    # The script lives in code/, so root is one level up
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "results"
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_project_directories()