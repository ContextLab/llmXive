import os
import sys
from pathlib import Path

def create_structure():
    """
    Create the root project directories for the llmXive science pipeline.
    
    Creates:
        - code/
        - data/
        - tests/
        - state/
        - results/
        - contracts/
    """
    root = Path(".")
    
    directories = [
        "code",
        "data",
        "tests",
        "state",
        "results",
        "contracts"
    ]
    
    created_dirs = []
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    return created_dirs

if __name__ == "__main__":
    created = create_structure()
    if created:
        print(f"\nSuccessfully created {len(created)} root directories.")
    else:
        print("\nAll root directories already exist.")
