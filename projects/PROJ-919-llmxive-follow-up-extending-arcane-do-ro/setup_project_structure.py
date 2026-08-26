import os
from pathlib import Path
import sys

def setup_directories():
    """
    Creates the required project directory structure for llmXive.
    Ensures all necessary folders exist, creating them if they don't.
    """
    base_dir = Path(__file__).parent
    
    # Define the directory structure
    directories = [
        "src",
        "src/lib",
        "src/services",
        "src/models",
        "src/analysis",
        "src/cli",
        "src/scripts",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/derived",
        "data/gold_standard",
        "artifacts",
        "specs",
        "specs/001-gene-regulation",
        "specs/001-gene-regulation/contracts",
        "figures",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create __init__.py files to make directories proper Python packages
    init_files = [
        "src/__init__.py",
        "src/lib/__init__.py",
        "src/services/__init__.py",
        "src/models/__init__.py",
        "src/analysis/__init__.py",
        "src/cli/__init__.py",
        "src/scripts/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]
    
    for init_file in init_files:
        full_path = base_dir / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created init file: {full_path}")
            created_count += 1
    
    print(f"\nProject structure setup complete. {created_count} items created.")
    return True

if __name__ == "__main__":
    setup_directories()
