import os
from pathlib import Path

def main():
    """
    Create required data and output directories for the project.
    Implements T001a: Execute Directory Creation.
    
    Creates:
      - data/raw
      - data/distorted
      - data/outputs
      - data/metadata
      - output/control
      - output/distorted
    """
    project_root = Path(__file__).parent.parent
    
    # Define the directories to create relative to the project root
    directories = [
        "data/raw",
        "data/distorted",
        "data/outputs",
        "data/metadata",
        "output/control",
        "output/distorted"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory creation complete. New directories created: {created_count}")
    return 0

if __name__ == "__main__":
    exit(main())