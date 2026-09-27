import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    This script ensures that the data and artifact directories exist
    before any data processing or visualization tasks are executed.
    """
    base_path = Path.cwd()
    
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "spot_check",
        base_path / "artifacts",
        base_path / "tests",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All required directories already exist.")

if __name__ == "__main__":
    main()