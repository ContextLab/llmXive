"""
T001: Initialize Project Directory Structure

Creates the required directory structure for the PROJ-308-quantifying-entanglement-entropy-in-rand project.
This script must be run from the project root.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to where this script is run from.
    # The task specifies creating directories in `projects/PROJ-308-quantifying-entanglement-entropy-in-rand/`.
    # Assuming this script is run from the repository root or the project root.
    # We will define the target base directory explicitly.
    project_base = Path("projects/PROJ-308-quantifying-entanglement-entropy-in-rand")
    
    directories = [
        "code",
        "data",
        "state",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state/projects",
    ]

    created_count = 0
    existing_count = 0

    print(f"Initializing project structure at: {project_base.absolute()}")

    for dir_path in directories:
        full_path = project_base / dir_path
        
        if full_path.exists():
            existing_count += 1
            print(f"  [SKIP] {dir_path} (already exists)")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"  [CREATED] {dir_path}")

    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")
    
    # Verification step as requested in task description
    print("\nVerifying structure with 'find' equivalent:")
    for root, dirs, files in os.walk(project_base):
        level = root.replace(str(project_base), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        # Only print directories to keep output clean, matching 'find -type d' logic
        for d in dirs:
            print(f"{subindent}{d}/")

    return 0

if __name__ == "__main__":
    sys.exit(main())