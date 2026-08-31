"""
Setup script to create the project directory structure.
Creates the required directories for code, data, and tests.
"""
import os
from pathlib import Path

def main():
    """Create the directory structure for the project."""
    project_root = Path(__file__).parent.parent
    
    # Define the directories to create relative to project root
    # Note: The task asks for 'code/' structure, so we create under code/
    base_dir = project_root / "code"
    
    directories = [
        base_dir,
        base_dir / "src",
        base_dir / "tests",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "results",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")
    
    if created_count == 0:
        print("All directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")
    
    # Verification
    if not (base_dir / "src").exists():
        print("ERROR: code/src directory was not created!")
        return 1
    
    print("Directory structure verification passed.")
    return 0

if __name__ == "__main__":
    exit(main())
