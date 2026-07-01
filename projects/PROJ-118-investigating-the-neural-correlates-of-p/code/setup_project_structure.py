"""
Setup script to create the project directory structure for PROJ-118.
This script creates the necessary folders as defined in plan.md.
"""
import os
from pathlib import Path

def main():
    # Project root directory
    project_root = Path("projects/PROJ-118-investigating-the-neural-correlates-of-p")
    
    # Directories to create as per plan.md
    directories = [
        "data/raw",
        "data/processed",
        "results",
        "results/plots",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
    ]
    
    # Create each directory
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")
    
    # Verify structure
    print("\nProject structure created successfully at:", project_root)
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path}")

if __name__ == "__main__":
    main()