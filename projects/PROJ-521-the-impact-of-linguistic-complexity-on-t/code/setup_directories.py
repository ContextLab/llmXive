"""
Script to create the required directory structure for the project.
This script ensures all necessary folders exist under the project root.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the script location or current working directory
    # The task specifies the project is at `projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/`
    # We assume the script is run from the repository root or the project root.
    # To be safe, we create the structure relative to the current working directory.
    
    project_root = Path.cwd()
    
    # If we are inside the project directory, use it directly.
    # If we are in the parent repo, we might need to navigate.
    # However, the task says "in projects/PROJ-521...". 
    # Let's assume the user runs this from the repo root and we target that specific path.
    
    target_path = project_root / "projects" / "PROJ-521-the-impact-of-linguistic-complexity-on-t"
    
    # If the target path doesn't exist, we might be running from inside it or need to create the parent.
    # Let's check if we are already in the project folder by looking for a marker (like code/)
    if (project_root / "code").exists() and (project_root / "data").exists():
        target_path = project_root
        print(f"Detected project root at: {target_path}")
    else:
        # Create the project root if it doesn't exist
        target_path.mkdir(parents=True, exist_ok=True)
        print(f"Created project root at: {target_path}")

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/outputs/figures",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = target_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nSetup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()