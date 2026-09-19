"""
Script to initialize the project directory structure.
Creates required directories and __init__.py files.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directories required by the project
    base_dirs = [
        "src",
        "tests",
        "data",
        "figures",
        "logs",
        "report",
        "artifacts"
    ]
    
    # Define subdirectories that need __init__.py
    init_dirs = [
        "src",
        "tests"
    ]
    
    # Create base directories
    for dir_name in base_dirs:
        dir_path = Path(dir_name)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files in src and tests
    for dir_name in init_dirs:
        init_path = Path(dir_name) / "__init__.py"
        # Create empty __init__.py
        init_path.touch(exist_ok=True)
        print(f"Created {init_path}")
    
    # Create specific subdirectories mentioned in T011 (data/processed)
    processed_dir = Path("data") / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {processed_dir}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()