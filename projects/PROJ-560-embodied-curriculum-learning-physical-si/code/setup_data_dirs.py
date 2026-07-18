import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create required data directories for the project."""
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-560-embodied-curriculum-learning-physical-si"
    
    # Define the base data path relative to the project root
    base_data_path = project_root / project_name / "data"
    
    directories = [
        base_data_path / "raw",
        base_data_path / "processed",
        base_data_path / "synthetic",
        base_data_path / "derivation_logs",
    ]
    
    for directory in directories:
        create_directory(directory)
    
    print("Data directory setup complete.")

if __name__ == "__main__":
    main()