import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure.
    
    Creates the following directories relative to the project root:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - data/simulations/
    - data/reports/
    - docs/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Determine project root (parent of the code/ directory)
    # Assuming this script is run from the project root or code/ directory
    if 'code' in Path(__file__).parts:
        # Script is inside code/ directory
        project_root = Path(__file__).parent.parent
    else:
        # Script is in project root
        project_root = Path(__file__).parent

    # Define the required directories
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/reports",
        "docs"
    ]

    created_count = 0
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
                created_count += 1
            except OSError as e:
                print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
                return False
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count > 0:
        print(f"Successfully created {created_count} directory/directories.")
    else:
        print("All directories already existed.")

    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
