"""
Script to create the required directory structure for the project.
This ensures data/raw, data/processed, data/split, and artifact directories exist.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    project_root = Path("projects/PROJ-240-predicting-the-impact-of-cold-work-on-re")
    
    # Create root directories
    (project_root / "code").mkdir(parents=True, exist_ok=True)
    (project_root / "tests").mkdir(parents=True, exist_ok=True)
    (project_root / "data").mkdir(parents=True, exist_ok=True)
    (project_root / "artifacts").mkdir(parents=True, exist_ok=True)
    
    # Create data subdirectories
    (project_root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "split").mkdir(parents=True, exist_ok=True)
    
    # Create artifact subdirectories
    (project_root / "artifacts" / "models").mkdir(parents=True, exist_ok=True)
    (project_root / "artifacts" / "reports").mkdir(parents=True, exist_ok=True)
    (project_root / "artifacts" / "figures").mkdir(parents=True, exist_ok=True)
    
    print("Directory structure created successfully.")

if __name__ == "__main__":
    main()
