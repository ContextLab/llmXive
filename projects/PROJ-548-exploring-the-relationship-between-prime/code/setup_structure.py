"""
Project Structure Initialization Script.

This script creates the directory structure required for the llmXive
research project PROJ-548. It ensures all necessary folders for data,
analysis, utilities, tests, and state management exist.
"""

import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure.
    
    Creates the following relative paths from the project root:
    - src/data/, src/analysis/, src/utils/, src/cli/
    - tests/unit/, tests/integration/
    - data/raw/, data/processed/, data/results/
    - results/
    - state/
    """
    # Define the base directory (project root)
    # We assume this script is run from the project root or a known location.
    # For safety, we create relative to the script's parent if not in a subfolder,
    # but the requirement says "relative to project root".
    # We will assume the current working directory is the project root.
    base_dir = Path.cwd()
    
    required_dirs = [
        "src/data",
        "src/analysis",
        "src/utils",
        "src/cli",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "results",
        "state"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure in: {base_dir}")
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
            skipped_count += 1

    print(f"\nStructure initialization complete.")
    print(f"Created: {created_count}, Skipped (already existed): {skipped_count}")
    
    # Verify structure
    missing = []
    for dir_path in required_dirs:
        if not (base_dir / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"\nError: The following directories are missing: {missing}")
        sys.exit(1)
    else:
        print("Verification: All required directories are present.")

if __name__ == "__main__":
    main()