import os
import sys
from typing import List

def create_directories() -> List[str]:
    """
    Create the project directory structure as defined in T001a, T001b, T001c.
    Returns a list of created directory paths.
    """
    # Define all required directories based on tasks T001a, T001b, T001c
    directories = [
        # T001a: Code structure
        "code",
        "code/ingest",
        "code/features",
        "code/models",
        "code/viz",
        "code/utils",
        
        # T001b: Data structure
        "data/raw",
        "data/processed",
        "data/artifacts",
        
        # T001c: State structure
        "state",
        
        # Additional required for tests (T001a extension)
        "tests",
        "tests/integration",
    ]

    created = []
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    return created

if __name__ == "__main__":
    print("Setting up project directory structure...")
    created_dirs = create_directories()
    print(f"Successfully created {len(created_dirs)} directories.")
    print("Directory structure ready.")
