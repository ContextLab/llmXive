"""
Setup script to initialize the project directory structure.
Creates: code/, data/, results/, tests/, docs/
"""
import os
from pathlib import Path

def main():
    """Create the required project directories."""
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data",
        "results",
        "tests",
        "docs"
    ]
    
    created = []
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create subdirectories for data organization
    data_subdirs = [
        "data/raw",
        "data/processed",
        "data/figures"
    ]
    for dir_name in data_subdirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
            print(f"Created directory: {dir_path}")
    
    # Create results subdirectories
    results_subdirs = [
        "results/models",
        "results/models/ensemble",
        "results/models/mc_dropout",
        "results/figures"
    ]
    for dir_name in results_subdirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
            print(f"Created directory: {dir_path}")
    
    # Create tests subdirectories
    tests_subdirs = [
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    for dir_name in tests_subdirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
            print(f"Created directory: {dir_path}")
    
    if created:
        print(f"\nSuccessfully created {len(created)} directories.")
    else:
        print("\nAll directories already exist.")

if __name__ == "__main__":
    main()
