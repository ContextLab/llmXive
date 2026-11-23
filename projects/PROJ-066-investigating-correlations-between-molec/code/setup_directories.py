import os
from pathlib import Path

def setup_directories():
    """
    Creates all required project directories for PROJ-066.
    This function ensures the existence of raw/processed data,
    code modules, models, tests, and state directories.
    """
    # Define the project root relative to this script's location
    # Assuming this script is at: projects/PROJ-.../code/setup_directories.py
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    directories = [
        # Data directories
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        
        # Code module directories
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "utils",
        project_root / "code" / "contracts",
        
        # Tests directory
        project_root / "tests",
        
        # State directory
        project_root.parent / "state" / "projects",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All required directories already exist.")

    return True
