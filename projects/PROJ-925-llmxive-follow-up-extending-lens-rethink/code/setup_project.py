"""
Project Structure Initialization Script.

This script executes the creation of the required directory hierarchy for the
llmXive follow-up project. It ensures that 'data/' and 'code/' are sibling
directories at the project root, with their respective subfolders created
as specified in the task description.
"""

import os
import sys
from pathlib import Path

# Import project root configuration from the existing API surface
from config import get_project_root

def create_structure():
    """
    Create the required directory structure for the project.

    Directories created:
    - data/raw
    - data/processed
    - code
    - code/tests
    - code/utils
    - code/models
    - docs

    Note: 'data/' and 'code/' are siblings at the project root.
    """
    project_root = get_project_root()
    print(f"Initializing project structure at: {project_root}")

    # Define the directories to create relative to the project root
    # Using a list of relative paths to ensure consistent creation
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/tests",
        "code/utils",
        "code/models",
        "docs"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Structure creation complete. {created_count} new directories created.")

    # Verify the structure by listing immediate children of data/ and code/
    data_dir = project_root / "data"
    code_dir = project_root / "code"

    if data_dir.exists() and code_dir.exists():
        print("\nVerification - Sibling directories found:")
        print(f"  data/: {list(data_dir.iterdir())}")
        print(f"  code/: {list(code_dir.iterdir())}")
    else:
        raise RuntimeError("Critical: data/ or code/ directory missing after creation.")

def main():
    """Entry point for the script."""
    try:
        create_structure()
        return 0
    except Exception as e:
        print(f"Error during structure creation: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())