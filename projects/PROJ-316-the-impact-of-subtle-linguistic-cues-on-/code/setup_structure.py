"""
Setup script to create the project directory structure and initialization files.
This script fulfills task T002.
"""
import os
from pathlib import Path

def main():
    """Create the project structure per implementation plan."""
    base_dir = Path(__file__).parent.parent
    
    # Define the required directories relative to the project root
    # Note: The task asks for `src/`, `tests/`, etc. at the root.
    # We will create them relative to the project root (parent of code/).
    
    dirs_to_create = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/derived",
        "code"
    ]
    
    # Create directories
    for dir_path in dirs_to_create:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py in src/ and its subfolders
    # Based on existing API, we know we need:
    # src/utils/, src/extraction/, src/analysis/
    # We will create these standard subfolders and their __init__.py files.
    
    src_subdirs = [
        "src/utils",
        "src/extraction",
        "src/analysis",
        "src/config" # For config.py location if needed, though often root
    ]
    
    for subdir in src_subdirs:
        full_path = base_dir / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created empty __init__.py: {init_file}")
        else:
            print(f"__init__.py already exists: {init_file}")
    
    # Ensure tests has __init__.py
    tests_init = base_dir / "tests" / "__init__.py"
    if not tests_init.exists():
        tests_init.touch()
        print(f"Created empty __init__.py: {tests_init}")

    # Ensure data subdirs have __init__.py if they are treated as packages (optional but good practice)
    # The task specifically said "Create empty __init__.py files in all src/ subfolders."
    # It did not explicitly demand them in data/ or tests/, but creating them in src/ is mandatory.
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
