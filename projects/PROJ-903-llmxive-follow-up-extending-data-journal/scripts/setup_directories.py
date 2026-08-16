"""
Script to initialize the required data directory structure for the project.
Creates: data/raw/, data/processed/, and output/ directories.
"""
import os
from pathlib import Path

def main():
    # Define the project root based on the task context
    # The task specifies paths relative to the project root:
    # projects/PROJ-903-llmxive-follow-up-extending-data-journal/
    project_root = Path("projects/PROJ-903-llmxive-follow-up-extending-data-journal")
    
    # Ensure the project root exists (though it should from previous tasks)
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Define the required directories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "output"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {directory}")
    
    print(f"Setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
