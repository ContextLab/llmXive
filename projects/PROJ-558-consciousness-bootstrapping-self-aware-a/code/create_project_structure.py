import os
from pathlib import Path

def create_structure(base_path: str = "projects/PROJ-558-consciousness-bootstrapping-self-aware-a") -> None:
    """
    Creates the directory structure for the Consciousness Bootstrapping project.
    
    Args:
        base_path: The root directory for the project structure.
    """
    root = Path(base_path)
    
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/checkpoints",
        "artifacts/results",
    ]
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    create_structure()
