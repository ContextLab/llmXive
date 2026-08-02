"""
Project structure setup script for PROJ-044.
Creates the required directory tree for the Differential Privacy in Federated Learning project.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as specified in the implementation plan.
    All paths are relative to the project root.
    """
    # Define the base path (assuming script is run from project root)
    # If run from code/, we need to adjust, but standard practice is run from root.
    base_path = Path.cwd()
    
    # Define all required directories
    directories = [
        "code/data",
        "code/training",
        "code/analysis",
        "code/models",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/partitions",
        "results",
        "artifacts"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            skipped_count += 1
    
    print(f"\nSetup complete. Created: {created_count}, Skipped: {skipped_count}")
    return True

if __name__ == "__main__":
    print("Initializing project structure for PROJ-044...")
    success = create_directories()
    if not success:
        sys.exit(1)
    sys.exit(0)