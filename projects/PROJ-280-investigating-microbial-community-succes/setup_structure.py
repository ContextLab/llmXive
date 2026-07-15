"""
Script to initialize the project directory structure for PROJ-280.
Creates all required directories as per the implementation plan.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the script location or current working directory
    # The task specifies the root as projects/PROJ-280-investigating-microbial-community-succes/
    project_root = Path("projects/PROJ-280-investigating-microbial-community-succes")
    
    # Define the subdirectories to create
    # Based on T001a requirements:
    # data/raw, data/processed, data/config
    # code
    # tests/unit, tests/contract, tests/integration
    # state/projects
    # contracts
    subdirs = [
        "data/raw",
        "data/processed",
        "data/config",
        "code",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "state/projects",
        "contracts"
    ]

    created_count = 0
    
    print(f"Initializing project structure at: {project_root}")
    
    for subdir in subdirs:
        dir_path = project_root / subdir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
            created_count += 1
        except OSError as e:
            print(f"  Error creating {dir_path}: {e}")

    print(f"\nSuccessfully created {created_count} directories.")
    print(f"Project root: {project_root}")

if __name__ == "__main__":
    main()
