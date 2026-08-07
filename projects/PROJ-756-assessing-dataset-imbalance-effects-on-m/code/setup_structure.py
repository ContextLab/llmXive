"""
Setup script to create the required project directory structure.
This script implements task T001c (and related setup tasks) by ensuring
the 'code', 'data', 'tests', 'artifacts', 'results', and 'state' directories
exist under the project root.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the necessary directory structure for the project.
    
    Creates:
        - code/
        - data/
        - tests/
        - artifacts/
        - results/
        - state/
        - logs/
        - logs/archive/
        - data/raw/
        - data/processed/
        - data/synthetic/
        - results/shap_analysis/
        - figures/
    """
    # Determine the project root. 
    # We assume the script is run from the project root or the 'code' directory.
    # If running from 'code', we go up one level.
    current_path = Path(__file__).resolve()
    
    # Try to find the project root by looking for the 'code' directory relative to this file
    # or by checking if we are inside 'code'.
    if current_path.name == 'code':
        project_root = current_path.parent
    elif current_path.parent.name == 'code':
        project_root = current_path.parent.parent
    else:
        # Fallback: assume current working directory is project root
        project_root = Path.cwd()
    
    # Define relative paths to create
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "artifacts",
        "results",
        "results/shap_analysis",
        "state",
        "logs",
        "logs/archive",
        "figures",
        "contracts"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # print(f"Directory already exists: {full_path}")
            existing_count += 1
    
    print(f"Directory setup complete. Created: {created_count}, Existing: {existing_count}")
    return True

def main():
    """Entry point for the script."""
    success = create_directories()
    if success:
        print("Task T001c (and related setup) completed successfully.")
        sys.exit(0)
    else:
        print("Failed to complete directory setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()