"""
Project structure initialization for Dream-State Learning.
Creates the required directory hierarchy for code, data, tests, and logs.
"""
import os
import sys
from pathlib import Path

def create_directories(base_path: str = ".") -> None:
    """
    Creates the standard project directory structure.
    
    Args:
        base_path: The root directory where the structure will be created.
    """
    root = Path(base_path)
    
    # Define the required directory structure
    directories = [
        # Core code directories
        "code",
        "code/data",
        "code/models",
        "code/utils",
        "code/eval",
        "code/scripts",
        
        # Test directories
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        
        # Data directories
        "data",
        "data/raw",
        "data/checkpoints",
        "data/results",
        "data/logs",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure initialization complete.")
    print(f"Created {created_count} new directories.")
    
    # Create __init__.py files to make directories Python packages
    init_files = [
        "code/__init__.py",
        "code/data/__init__.py",
        "code/models/__init__.py",
        "code/utils/__init__.py",
        "code/eval/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py",
    ]
    
    for init_file in init_files:
        full_path = root / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created init file: {full_path}")

if __name__ == "__main__":
    # Default to current directory if no argument provided
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    create_directories(base)
