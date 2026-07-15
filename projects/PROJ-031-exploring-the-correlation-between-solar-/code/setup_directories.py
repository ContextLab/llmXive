import os
from pathlib import Path

def create_directory_structure():
    """
    Create the project directory structure for PROJ-031.
    
    Creates:
    - projects/PROJ-031-exploring-the-correlation-between-solar-/
      - code/
      - data/
        - raw/
        - processed/
      - results/
      - contracts/
      - tests/
    """
    project_root = Path("projects/PROJ-031-exploring-the-correlation-between-solar-")
    
    # Define directories to create
    directories = [
        project_root,
        project_root / "code",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "contracts",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    return project_root
