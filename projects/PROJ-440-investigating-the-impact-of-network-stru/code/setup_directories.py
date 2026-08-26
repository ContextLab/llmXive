import os
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure for the project.
    Implements T001a: Create directory structure.
    """
    base_path = Path(".")
    
    # Define the required directory paths relative to the project root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Note: We do not recreate if exists to avoid unnecessary noise,
        # but the existence of the directory satisfies the task requirement.
    
    print(f"Directory structure verified/created. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    setup_directories()
