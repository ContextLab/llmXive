import os
import sys
from pathlib import Path

def main():
    """
    Create project directory structure and initialize __init__.py files.
    
    Creates the following directories:
    - code/data, code/models, code/analysis, code/utils
    - data/raw, data/processed
    - results, tests
    
    And adds empty __init__.py files to each code/ subdirectory.
    """
    base_dir = Path(__file__).parent.parent
    
    # Define directories to create
    directories = [
        base_dir / "code" / "data",
        base_dir / "code" / "models",
        base_dir / "code" / "analysis",
        base_dir / "code" / "utils",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "results",
        base_dir / "tests",
    ]
    
    # Create directories
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files in code/ subdirectories
    code_subdirs = [
        base_dir / "code" / "data",
        base_dir / "code" / "models",
        base_dir / "code" / "analysis",
        base_dir / "code" / "utils",
    ]
    
    for dir_path in code_subdirs:
        init_file = dir_path / "__init__.py"
        init_file.touch(exist_ok=True)
        print(f"Created __init__.py: {init_file}")
    
    print("Project structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())