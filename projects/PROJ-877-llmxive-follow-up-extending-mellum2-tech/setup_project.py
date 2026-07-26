"""
Script to initialize the project directory structure for PROJ-877.
Creates the root directory and standard subdirectories (code, data, tests).
"""
import os
from pathlib import Path

def main():
    project_root = Path("projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech")
    
    # Define required directories
    required_dirs = [
        project_root,
        project_root / "code",
        project_root / "data",
        project_root / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "specs",
        project_root / "contracts",
        project_root / "figures",
    ]

    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")

    # Create .gitkeep files to ensure directories are tracked by git
    for dir_path in required_dirs:
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {dir_path}")

    print(f"\nProject structure initialized successfully at {project_root}")
    print(f"Total new directories created: {created_count}")

if __name__ == "__main__":
    main()