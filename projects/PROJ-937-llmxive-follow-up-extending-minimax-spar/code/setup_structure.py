"""
Project Structure Initialization Script for llmXive.

This script creates the required directory structure for the project
as specified in plan.md and tasks.md.

Directories created:
- code/
- data/raw
- data/processed
- results
- tests/unit
- tests/integration
- specs/ (for design documents)
- figures/ (for generated plots)
"""

import os
import sys

def create_project_structure():
    """Create the project directory structure."""
    # Define all required directories relative to project root
    directories = [
        "code",
        "code/utils",
        "code/data",
        "code/heuristics",
        "code/eval",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration",
        "specs",
        "figures"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        if os.path.exists(dir_path):
            print(f"[SKIP] Directory already exists: {dir_path}")
            existing_count += 1
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"[CREATE] Directory: {dir_path}")
            created_count += 1
    
    print(f"\nProject structure initialization complete.")
    print(f"Created: {created_count} directories")
    print(f"Skipped (already exist): {existing_count} directories")
    
    return created_count > 0 or existing_count > 0

if __name__ == "__main__":
    success = create_project_structure()
    sys.exit(0 if success else 1)