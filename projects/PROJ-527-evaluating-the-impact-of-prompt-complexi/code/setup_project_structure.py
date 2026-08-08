"""
Project structure initialization script.
Creates the required directory hierarchy for the llmXive research pipeline.
"""
import os
from pathlib import Path

def main():
    """Create project directories."""
    # Define base directories relative to the project root
    # The script assumes it is run from the project root or the code directory
    # We resolve the project root as the parent of the 'code' directory if this file is in code/
    
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # Assuming file is at code/setup_project_structure.py
    
    directories = [
        project_root / "code",
        project_root / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "state",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory exists: {directory.relative_to(project_root)}")
    
    if created_count == 0:
        print("All directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    main()
