import os
from pathlib import Path

def create_structure():
    """
    Creates the directory structure for the PROJ-558 project.
    
    Creates the following hierarchy relative to the project root:
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
    project_root = Path(__file__).parent.parent
    base_dir = project_root / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
    
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "code",
        base_dir / "tests",
        base_dir / "artifacts" / "checkpoints",
        base_dir / "artifacts" / "results",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Ensure the base directories exist for verification
    (base_dir / "data").mkdir(parents=True, exist_ok=True)
    (base_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    
    print(f"Project structure created at: {base_dir}")
    return base_dir

if __name__ == "__main__":
    create_structure()