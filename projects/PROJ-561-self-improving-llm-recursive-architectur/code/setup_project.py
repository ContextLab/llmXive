"""
Project setup script for llmXive automated science pipeline.
Creates the required directory structure and initializes __init__.py files.
"""
import os
import sys
from pathlib import Path

# Define the root directory (assumed to be the project root)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Define the directory structure to create
DIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "results",
    "specs",
    "tests",
    "tests/unit",
    "tests/integration",
]

def create_project_structure():
    """Create all required directories and __init__.py files."""
    created_dirs = []
    created_files = []

    for dir_name in DIRECTORIES:
        dir_path = ROOT_DIR / dir_name
        
        # Create directory if it doesn't exist
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path.relative_to(ROOT_DIR)))
            print(f"Created directory: {dir_path.relative_to(ROOT_DIR)}")
        
        # Create __init__.py in each directory
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            # Create an empty __init__.py or with a simple docstring
            init_file.write_text(f'"""\nInitialization file for {dir_path.name}.\n"""\n')
            created_files.append(str(init_file.relative_to(ROOT_DIR)))
            print(f"Created __init__.py: {init_file.relative_to(ROOT_DIR)}")
    
    print(f"\nSummary:")
    print(f"  Directories created: {len(created_dirs)}")
    print(f"  __init__.py files created: {len(created_files)}")
    return len(created_dirs) + len(created_files) > 0

if __name__ == "__main__":
    success = create_project_structure()
    if success:
        print("\nProject structure setup completed successfully.")
        sys.exit(0)
    else:
        print("\nProject structure already exists or no changes were made.")
        sys.exit(0)
