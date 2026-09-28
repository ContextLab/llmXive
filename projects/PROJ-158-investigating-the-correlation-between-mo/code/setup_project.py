import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure and initialize __init__.py files.
    This script is idempotent: running it multiple times will not fail.
    """
    # Define the project root (assuming this script is in code/ or project root)
    # We use the path relative to the script execution context to find the root.
    # Assuming the script is run from the project root or code/ directory.
    # Let's assume the root is the parent of 'code' if we are in code/, 
    # or the current directory if we are at root.
    
    # Strategy: Find the directory containing 'code' folder.
    current_path = Path(__file__).resolve().parent
    
    # Check if we are inside 'code'
    if current_path.name == 'code':
        root_dir = current_path.parent
    else:
        root_dir = current_path
    
    # Define relative directories to create
    # Based on T001 requirements:
    # code/data, code/models, code/analysis, code/utils
    # data/raw, data/processed
    # results, tests
    
    dirs_to_create = [
        root_dir / 'code' / 'data',
        root_dir / 'code' / 'models',
        root_dir / 'code' / 'analysis',
        root_dir / 'code' / 'utils',
        root_dir / 'data' / 'raw',
        root_dir / 'data' / 'processed',
        root_dir / 'results',
        root_dir / 'tests',
    ]
    
    # Directories that need __init__.py (only code/ subdirectories)
    # The task says: "create empty __init__.py files in each code/ subdirectory"
    # It also implies the root code directory might need one, and tests/data might need one too
    # to be valid python packages or just for structure.
    # We will create __init__.py in:
    # code/, code/data, code/models, code/analysis, code/utils
    # tests/, data/ (for consistency as packages)
    
    # Let's ensure the root code dir has one too if it doesn't
    code_root = root_dir / 'code'
    if not (code_root / '__init__.py').exists():
        (code_root / '__init__.py').touch()
        print(f"Created: {code_root / '__init__.py'}")
    
    # Initialize __init__.py in subdirectories
    for d in dirs_to_create:
        # Create directory if it doesn't exist
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {d}")
        else:
            # print(f"Directory already exists: {d}")
            pass
        
        # Create __init__.py for code/ subdirectories and tests/data roots
        # Requirement: "create empty __init__.py files in each code/ subdirectory"
        if d.is_relative_to(code_root) and d != code_root:
            init_file = d / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                print(f"Created: {init_file}")
        
        # Also ensure tests and data roots have __init__.py for package structure
        if d == root_dir / 'tests' or d == root_dir / 'data':
            init_file = d / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                print(f"Created: {init_file}")

    print("Project structure initialization complete.")

if __name__ == '__main__':
    main()