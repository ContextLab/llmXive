import os
from pathlib import Path

def create_structure():
    """
    Creates the directory structure for the consciousness bootstrapping project.
    
    Structure:
    projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── code/
    ├── tests/
    └── artifacts/
        ├── checkpoints/
        └── results/
    """
    base_path = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    directories = [
        base_path,
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "code",
        base_path / "tests",
        base_path / "artifacts" / "checkpoints",
        base_path / "artifacts" / "results",
        base_path / "artifacts" / "figures",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"\nTotal directories created: {created_count}")
    print(f"Project structure initialized at: {base_path}")
    
    return True

if __name__ == "__main__":
    create_structure()
