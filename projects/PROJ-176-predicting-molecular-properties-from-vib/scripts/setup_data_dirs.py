"""
Script to create the required project directory structure.
This script ensures all necessary folders exist for the project.
"""
import os
from pathlib import Path

def main():
    """Create the directory structure for the project."""
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the required directories
    directories = [
        base_dir / "code",
        base_dir / "tests",
        base_dir / "data" / "raw",
        base_dir / "data" / "preprocessed",
        base_dir / "data" / "external",
        base_dir / "specs" / "001-predicting-molecular-properties-from-vib",
        base_dir / "results",
        base_dir / "figures",
        base_dir / "state",
        base_dir / "runs",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    # Create .gitkeep files to ensure empty directories are tracked by git
    gitkeep_content = "# Placeholder to ensure directory exists in git\n"
    for directory in directories:
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text(gitkeep_content)
            print(f"Created .gitkeep in: {directory}")
    
    print(f"Setup complete. Created {created_count} directories.")

if __name__ == "__main__":
    main()