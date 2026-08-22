import os
import sys

def create_structure(base_dir="."):
    """
    Creates the project directory structure and initializes __init__.py files.
    
    Directories created:
    - src/
    - tests/unit/
    - tests/integration/
    - data/raw/
    - data/processed/
    - results/
    
    Files created:
    - src/__init__.py
    - tests/__init__.py
    - tests/unit/__init__.py
    - tests/integration/__init__.py
    """
    directories = [
        "src",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "results"
    ]
    
    init_files = [
        "src/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]
    
    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    for file_path in init_files:
        full_path = os.path.join(base_dir, file_path)
        # Ensure parent directory exists before creating file
        parent_dir = os.path.dirname(full_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                f.write("# Package initialization\n")
            print(f"Created file: {full_path}")
        else:
            print(f"File already exists: {full_path}")

if __name__ == "__main__":
    create_structure()
