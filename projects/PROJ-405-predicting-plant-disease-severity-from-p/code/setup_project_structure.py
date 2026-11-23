import os
from pathlib import Path
from typing import List

def create_structure() -> None:
    """
    Create the required project directory structure for PROJ-405.
    
    This function creates the following directories relative to the project root:
    - code/
    - data/
    - tests/
    - artifacts/
    
    It also ensures parent directories exist.
    """
    # Define the project root
    project_root = Path(__file__).resolve().parent.parent
    proj_405_root = project_root / "projects" / "PROJ-405"
    
    # Define required subdirectories
    required_dirs = [
        proj_405_root / "code",
        proj_405_root / "data",
        proj_405_root / "tests",
        proj_405_root / "artifacts",
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
    print(f"Created {created_count} directories under {proj_405_root}")

if __name__ == "__main__":
    create_structure()
