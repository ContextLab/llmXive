"""
Project Directory Initialization Script.

This script creates the required directory structure for the project,
including 'results/plots' and 'tests/contract' and 'tests/unit'.
It also ensures that 'data' and 'contracts' directories exist with
their required subdirectories as per the project plan (T009, T008).
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    
    # Define all required directories relative to project root
    # Based on T001, T008, T009, and T010 requirements
    directories = [
        # Core directories (T001)
        "code",
        "data",
        "results",
        "tests",
        "contracts",
        
        # Data subdirectories (T009)
        "data/raw",
        "data/processed",
        "data/metrics",
        "data/atlas",
        
        # Results subdirectories (T010)
        "results/plots",
        
        # Tests subdirectories (T010)
        "tests/contract",
        "tests/unit",
        
        # Contracts files (T008) - ensure directory exists
        "contracts",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(root)}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path.relative_to(root)}")

    # Create .gitkeep files to ensure directories are tracked by git
    # especially for empty directories like plots, contract, unit
    keep_files = [
        "results/plots/.gitkeep",
        "tests/contract/.gitkeep",
        "tests/unit/.gitkeep",
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "data/metrics/.gitkeep",
        "data/atlas/.gitkeep",
        "contracts/.gitkeep",
    ]

    for keep_path in keep_files:
        full_path = root / keep_path
        if not full_path.exists():
            full_path.touch()
            print(f"Created placeholder: {full_path.relative_to(root)}")

    print(f"\nInitialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    exit(main())
