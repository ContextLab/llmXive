import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure required for the llmXive pipeline.
    
    Creates:
      - code/
      - data/raw
      - data/processed
      - data/results
      - specs/contracts/
    
    Returns a list of created paths for verification.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/contracts"
    ]
    
    created_paths = []
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
        else:
            created_paths.append(str(full_path))
            # Optional: log that it already exists if needed
    
    # Print summary for verification
    print(f"Directory creation complete for project: {project_root}")
    print("Created/Verified directories:")
    for p in created_paths:
        print(f"  - {p}")
    
    return created_paths

if __name__ == "__main__":
    create_directories()
