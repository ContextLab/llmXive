import os
import sys
from pathlib import Path
from typing import List

def create_project_structure():
    """Create the project directory structure."""
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "artifacts/models",
        "artifacts/metrics",
        "tests",
        "specs/001-predict-tg-metallic-glasses/contracts",
        "code/config",
        "code/contracts"
    ]
    
    created = []
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        created.append(dir_path)
        print(f"Created directory: {dir_path}")
    
    # Create .gitkeep files
    gitkeep_dirs = ["data/raw", "data/processed"]
    for dir_path in gitkeep_dirs:
        gitkeep_path = Path(dir_path) / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created .gitkeep in: {dir_path}")
        created.append(str(gitkeep_path))
    
    return created

def main():
    """Main function for creating project structure."""
    print("Creating project structure...")
    created = create_project_structure()
    print(f"\nCreated {len(created)} items:")
    for item in created:
        print(f"  - {item}")
    return created

if __name__ == "__main__":
    main()
