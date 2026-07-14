import os
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure:
    code/data, code/analysis, code/config, code/tests
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        base_path / "code" / "data",
        base_path / "code" / "analysis",
        base_path / "code" / "config",
        base_path / "code" / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "figures",
        base_path / "specs",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    if created_count == 0:
        print("All directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")
    
    return True

if __name__ == "__main__":
    create_directories()