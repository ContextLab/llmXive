import os
from pathlib import Path

def create_structure():
    """
    Creates the directory structure for the Consciousness Bootstrapping project.
    
    Creates the following hierarchy relative to the project root:
    projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── code/
    ├── tests/
    ├── artifacts/
    │   ├── checkpoints/
    │   └── results/
    """
    # Define the base project directory
    base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define all required subdirectories
    directories = [
        base_dir,
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "code",
        base_dir / "tests",
        base_dir / "artifacts" / "checkpoints",
        base_dir / "artifacts" / "results",
    ]
    
    # Create directories
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            pass  # Directory already exists, no action needed
    
    return created_count

if __name__ == "__main__":
    count = create_structure()
    print(f"Created {count} directories.")
