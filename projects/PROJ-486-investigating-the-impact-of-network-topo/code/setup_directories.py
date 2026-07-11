import os
import sys

def create_directories():
    """
    Create the required project directory structure for PROJ-486.
    
    Creates:
    - code/
    - data/
    - data/raw/
    - data/processed/
    - data/visualizations/
    - tests/
    - tests/unit/
    - tests/integration/
    - docs/
    """
    base_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/visualizations",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Directory setup complete. Created {created_count} new directories.")
    return created_count

if __name__ == "__main__":
    create_directories()
