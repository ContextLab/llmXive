import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-328.
    
    Creates the following directories relative to the project root:
    - projects/PROJ-328-predicting-the-impact-of-composition-on-/data/
    - projects/PROJ-328-predicting-the-impact-of-composition-on-/code/
    - projects/PROJ-328-predicting-the-impact-of-composition-on-/tests/
    - projects/PROJ-328-predicting-the-impact-of-composition-on-/models/
    
    Also creates subdirectories for data organization:
    - data/raw
    - data/processed
    - data/outputs
    - data/checksums
    """
    # Define the project root relative to this script's location
    # Assuming this script is at projects/PROJ-328-predicting-the-impact-of-composition-on-/code/setup_project_structure.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Ensure we are in the correct project directory
    expected_project_name = "PROJ-328-predicting-the-impact-of-composition-on-"
    if project_root.name != expected_project_name:
        print(f"Warning: Expected project directory name '{expected_project_name}', found '{project_root.name}'")
        print(f"Proceeding with directory creation in: {project_root}")
    
    # Define the directories to create
    directories = [
        "data",
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/checksums",
        "code",
        "tests",
        "models",
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    print(f"Project root: {project_root}")
    
    # Verify structure
    print("\nVerifying directory structure:")
    for dir_name in directories:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [MISSING] {dir_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())