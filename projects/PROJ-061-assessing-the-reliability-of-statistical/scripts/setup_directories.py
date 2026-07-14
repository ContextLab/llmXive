"""
Script to create the required directory structure for the project.
This script ensures that all necessary directories and __init__.py files
exist as per the project specification.
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    
    # Define required directories relative to project root
    dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs",
    ]
    
    created_count = 0
    for dir_path in dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    # Ensure __init__.py files exist in Python packages
    python_packages = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    for pkg in python_packages:
        init_file = project_root / pkg / "__init__.py"
        if not init_file.exists():
            # Create a minimal __init__.py
            init_file.write_text('"""\n' + pkg + " package.\n\"\"\"\n")
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py exists: {init_file}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()