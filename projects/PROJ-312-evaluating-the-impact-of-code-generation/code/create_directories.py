"""
T008: Create directory structure for the project.
Creates: data/raw/, data/processed/, data/spot_check/, artifacts/, tests/
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "data/raw",
        "data/processed",
        "data/spot_check",
        "artifacts",
        "tests"
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    print("Directory structure creation complete.")

if __name__ == "__main__":
    main()