import os
import sys
from pathlib import Path
from typing import List

def setup_data_directories() -> List[str]:
    """
    Creates the project directory structure as specified in the implementation plan.
    
    Returns a list of created directory paths.
    """
    # Define the project root based on the task requirement
    project_root = Path("projects/PROJ-884-llmxive-follow-up-extending-self-improvi")
    
    # Define the directory structure to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code" / "dataset",
        project_root / "code" / "symbolic",
        project_root / "code" / "bes",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]
    
    created_dirs = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
        else:
            created_dirs.append(str(dir_path))
    
    return created_dirs

def main():
    """Main entry point for the script."""
    print("Creating project directory structure...")
    created = setup_data_directories()
    print(f"Successfully created {len(created)} directories:")
    for d in created:
        print(f"  - {d}")
    print("Done.")

if __name__ == "__main__":
    main()
