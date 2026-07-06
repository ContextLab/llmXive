"""
Script to create the project directory structure.
"""
import os
from pathlib import Path

def create_project_directories(project_root: str = "projects/PROJ-530-neural-correlates-of-error-monitoring-du") -> None:
    """
    Create the standard project directory structure.
    
    Args:
        project_root: Root path for the project.
    """
    root = Path(project_root)
    
    # Data directories
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    
    # Results directories
    (root / "results" / "models").mkdir(parents=True, exist_ok=True)
    (root / "results" / "figures").mkdir(parents=True, exist_ok=True)
    (root / "results" / "diagnostics").mkdir(parents=True, exist_ok=True)
    
    # Code and tests
    (root / "code").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    
    # Specs
    (root / "specs").mkdir(parents=True, exist_ok=True)
    
    print(f"Created directory structure at: {root.resolve()}")

if __name__ == "__main__":
    create_project_directories()