"""
Setup script to create the data/processed/ directory for project PROJ-920.

This script ensures the `data/processed/` directory exists within the project root.
It is idempotent: running it multiple times will not raise errors if the directory
already exists.
"""
import os
from pathlib import Path

# Define the project root relative to this script's location or explicitly
# Based on task description: projects/PROJ-920-llmxive-follow-up-extending-masking-stal/
# We assume the script is run from the project root or we construct the path relative to a known base.
# To be robust, we define the target path explicitly as requested.

PROJECT_ROOT = Path("projects/PROJ-920-llmxive-follow-up-extending-masking-stal")
TARGET_DIR = PROJECT_ROOT / "data" / "processed"

def main():
    """Create the data/processed/ directory if it does not exist."""
    try:
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Successfully ensured directory exists: {TARGET_DIR}")
        # Verify existence
        if TARGET_DIR.is_dir():
            print(f"Verification: {TARGET_DIR} is a valid directory.")
        else:
            print(f"Error: Directory creation failed or path is invalid.")
            return 1
    except PermissionError:
        print(f"Error: Permission denied when trying to create {TARGET_DIR}")
        return 1
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())