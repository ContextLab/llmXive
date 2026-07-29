import os
from pathlib import Path

def create_structure():
    """
    Creates the directory structure for project PROJ-558-consciousness-bootstrapping-self-aware-a.
    
    Creates the following hierarchy:
    projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
        ├── data/
        │   ├── raw/
        │   └── processed/
        ├── code/
        ├── tests/
        ├── artifacts/
        │   ├── checkpoints/
        │   └── results/
        └── docs/ (optional, for future documentation)
    """
    base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define the directory structure relative to base_dir
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/checkpoints",
        "artifacts/results",
        "docs"
    ]
    
    created_dirs = []
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        except PermissionError:
            print(f"Permission denied creating directory: {full_path}")
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}")
    
    if not created_dirs:
        print("No directories were created. They may already exist or errors occurred.")
    else:
        print(f"Successfully created {len(created_dirs)} directories.")
    
    return created_dirs

if __name__ == "__main__":
    create_structure()
