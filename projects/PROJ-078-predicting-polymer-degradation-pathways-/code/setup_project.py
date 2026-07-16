"""
Script to initialize the project directory structure for llmXive PROJ-078.

Creates the following directories relative to the project root:
- code/
- data/raw/
- data/processed/
- data/reports/
- tests/
- state/

This script ensures that all necessary folders exist before other tasks
begin implementation.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the required project directory structure."""
    # Define the base directories relative to the project root
    # We assume the script is run from the project root or the parent of 'code'
    # To be safe, we determine the root based on where this script lives or cwd.
    # Standard convention: script is in 'code/', root is parent.
    
    script_path = Path(__file__).resolve()
    # If script is in code/, root is parent. If script is in root, root is current.
    # Given the task asks to create 'code/', we assume we are running from root
    # or we create 'code' relative to the current working directory.
    
    root_dir = Path.cwd()
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    created = []
    skipped = []
    
    for dir_name in directories:
        full_path = root_dir / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
            print(f"Created directory: {full_path}")
        else:
            skipped.append(dir_name)
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSummary: Created {len(created)} directories, skipped {len(skipped)}.")
    return 0

if __name__ == "__main__":
    sys.exit(create_directories())
