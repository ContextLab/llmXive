import os
from pathlib import Path

def create_directories():
    """
    Create the required directory structure for the project.
    This function ensures all necessary folders exist before data processing begins.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    # Define the directory structure relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/features",
        "tests",
        "state/projects",
        "specs/001-structure-property-relationships/contracts",
        "figures",
        "logs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # else: pass (directory already exists)
    
    return created_count

if __name__ == "__main__":
    count = create_directories()
    print(f"Directory creation complete. Created {count} new directories.")
