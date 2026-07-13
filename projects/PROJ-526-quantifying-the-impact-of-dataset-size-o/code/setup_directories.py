import os
from pathlib import Path

def create_directories():
    """
    Create the required directory structure for the project.
    Specifically creates subdirectories for data and tests as per T001b.
    """
    # Define the base project root (assuming script runs from project root or code/)
    # We use the current working directory as the project root context
    project_root = Path.cwd()
    
    # Define relative paths for T001b
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    create_directories()