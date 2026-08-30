"""
Script to initialize the project directory structure for PROJ-260.
Creates the required directories: src/, tests/, data/, outputs/
and their subdirectories as defined in the implementation plan.
"""

import os
import sys

# Define the project root relative to this script's location
# Assuming this script is at: code/scripts/setup_project.py
# Project root is: code/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Directory structure to create
# Based on tasks.md and plan.md requirements
directories = [
    # Source code structure
    "src/models",
    "src/services",
    "src/lib",
    "src/cli",
    
    # Test structure
    "tests/unit",
    "tests/integration",
    "tests/contract",
    
    # Data structure (following data-model.md conventions)
    "data/raw",
    "data/derived/topology",
    "data/derived/vdos",
    "data/derived/reference",
    "data/derived/correlation",
    "data/metadata",
    
    # Outputs structure
    "outputs/reports",
    "outputs/figures",
    
    # Additional standard directories
    "code/scripts",
    "code/config",
]

def create_directories():
    """Create all required directories."""
    created = []
    errors = []

    for dir_path in directories:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        try:
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                created.append(dir_path)
                print(f"Created directory: {dir_path}")
            else:
                print(f"Directory already exists: {dir_path}")
        except OSError as e:
            error_msg = f"Failed to create {dir_path}: {e}"
            errors.append(error_msg)
            print(f"ERROR: {error_msg}")

    return created, errors

def main():
    """Main entry point."""
    print(f"Project Root: {PROJECT_ROOT}")
    print("=" * 50)
    print("Initializing project structure...")
    print("=" * 50)

    created, errors = create_directories()

    print("=" * 50)
    print(f"Successfully created: {len(created)} directories")
    
    if errors:
        print(f"Failed to create: {len(errors)} directories")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Project structure initialization complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()