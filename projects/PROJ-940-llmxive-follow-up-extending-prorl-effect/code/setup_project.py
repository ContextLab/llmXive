import os
import sys

def create_structure():
    """
    Creates the standard project directory structure and initializes
    necessary __init__.py and .gitkeep files.
    """
    # Define the base directories relative to the project root
    base_dirs = [
        "code/src",
        "code/tests/unit",
        "code/tests/integration",
        "code/data/raw",
        "code/data/processed",
        "code/results"
    ]

    # Create directories
    for dir_path in base_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create __init__.py files
    init_files = [
        "code/src/__init__.py",
        "code/tests/__init__.py",
        "code/tests/unit/__init__.py",
        "code/tests/integration/__init__.py"
    ]

    for file_path in init_files:
        # Ensure parent directory exists before creating file
        parent_dir = os.path.dirname(file_path)
        os.makedirs(parent_dir, exist_ok=True)
        
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write("")
            print(f"Created empty file: {file_path}")
        else:
            print(f"File already exists (skipped): {file_path}")

    # Create .gitkeep files for data directories
    gitkeep_files = [
        "code/data/raw/.gitkeep",
        "code/data/processed/.gitkeep",
        "code/results/.gitkeep"
    ]

    for file_path in gitkeep_files:
        parent_dir = os.path.dirname(file_path)
        os.makedirs(parent_dir, exist_ok=True)
        
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write("# Keep this directory in git")
            print(f"Created .gitkeep file: {file_path}")
        else:
            print(f"File already exists (skipped): {file_path}")

    print("Project structure creation complete.")

if __name__ == "__main__":
    create_structure()