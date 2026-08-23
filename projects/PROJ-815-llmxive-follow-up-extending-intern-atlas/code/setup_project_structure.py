"""
Script to create the project directory structure for PROJ-815.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required directory tree."""
    project_root = Path("projects/PROJ-815-llmxive-follow-up-extending-intern-atlas")
    
    # Define the directories to create based on the task description
    # Using the relative paths from the task: code/data, code/models, code/analysis, code/utils, data/raw, data/processed, tests/unit, tests/integration
    # We assume 'code' and 'data' and 'tests' are relative to the project_root
    
    subdirs = [
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    for subdir in subdirs:
        full_path = project_root / subdir
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}")
            return 1
    
    print(f"Successfully created {created_count} directories under {project_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())