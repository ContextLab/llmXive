"""
Task T001a: Create project directory structure.
Creates directories data/raw, data/processed, code, tests, docs
under projects/PROJ-379-predicting-molecular-excitation-waveleng/.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the task description
    # We assume the script is run from the repository root or project root
    # The task specifies the path: projects/PROJ-379-predicting-molecular-excitation-waveleng/
    project_name = "PROJ-379-predicting-molecular-excitation-waveleng"
    project_root = Path("projects") / project_name

    # Ensure the project root exists
    project_root.mkdir(parents=True, exist_ok=True)
    print(f"Project root ensured: {project_root}")

    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs"
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {full_path}")
        created_count += 1

    print(f"Successfully created/verified {created_count} directories.")
    
    # Optional: Create a marker file to indicate initialization
    marker_file = project_root / ".initialized"
    if not marker_file.exists():
        marker_file.touch()
        print(f"Created marker file: {marker_file}")

if __name__ == "__main__":
    main()
