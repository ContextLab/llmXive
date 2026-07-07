"""
Setup script for creating the project directory structure.
This script ensures all required directories exist for data storage,
code organization, and testing.
"""

import os
import sys

# Define the base project directory (parent of the code folder)
# Assuming this script is run from the project root or code/
# We need to resolve the root relative to this file's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Directories to create relative to PROJECT_ROOT
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/models",
    "code",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/perf",
    "docs",
    "docs/reports",
    "specs",
    "specs/001-molecular-topology-selectivity"
]

def setup_directories():
    """Create all required directories if they do not exist."""
    created_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Project Root: {PROJECT_ROOT}")
    print("-" * 40)

    for dir_path in DIRECTORIES:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        
        if os.path.exists(full_path):
            print(f"[SKIP] {dir_path} (already exists)")
            skipped_count += 1
        else:
            try:
                os.makedirs(full_path, exist_ok=True)
                print(f"[CREATE] {dir_path}")
                created_count += 1
            except OSError as e:
                print(f"[ERROR] Failed to create {dir_path}: {e}")
                error_count += 1

    print("-" * 40)
    print(f"Summary: Created={created_count}, Skipped={skipped_count}, Errors={error_count}")
    
    if error_count > 0:
        print("Setup completed with errors.")
        return False
    
    print("Directory structure setup successful.")
    return True

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)