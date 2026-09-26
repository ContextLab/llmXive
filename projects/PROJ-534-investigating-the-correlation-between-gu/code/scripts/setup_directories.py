"""
Script to create the project directory structure for PROJ-534.
This implements Task T001a: Create project directory structure.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to this script's location
# The script is at code/scripts/setup_directories.py
# The project root is code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory structure to create
DIRECTORIES = [
    "src",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "data/raw",
    "data/processed",
    "data/results",
    "logs",
    "figures",
    "contracts",
    "specs",
]

def main():
    """Create all required directories."""
    print(f"Project root detected at: {PROJECT_ROOT}")
    
    created_count = 0
    for dir_name in DIRECTORIES:
        target_path = PROJECT_ROOT / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path.relative_to(PROJECT_ROOT)}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path.relative_to(PROJECT_ROOT)}")
    
    print(f"\nDirectory structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())