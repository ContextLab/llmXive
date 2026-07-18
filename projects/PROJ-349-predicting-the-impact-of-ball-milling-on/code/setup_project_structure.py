"""
Script to create the project directory structure for the ball milling PSD project.
Creates all required directories under the project root.
"""
import os
import sys
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.
    Returns the list of created directories.
    """
    # Define the project root (current directory)
    root = Path.cwd()
    
    # Define all required directories relative to root
    directories = [
        "code",
        "code/src",
        "code/src/config",
        "code/src/ingest",
        "code/src/preprocess",
        "code/src/model",
        "code/src/evaluate",
        "code/src/interpret",
        "code/src/cli",
        "code/src/utils",
        "code/tests",
        "code/tests/unit",
        "code/tests/contract",
        "code/tests/integration",
        "code/data/raw",
        "code/data/processed",
        "code/data/splits",
        "code/results",
        "code/contracts",
        "code/.github/workflows",
        "code/specs",
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked by git
    gitkeep_dirs = [
        "code/data/raw",
        "code/data/processed",
        "code/data/splits",
        "code/results",
    ]
    for dir_path in gitkeep_dirs:
        full_path = root / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.touch()
            print(f"Created .gitkeep in: {full_path}")
    
    print(f"\nProject structure setup complete. Created {len(created)} directories.")
    return created

if __name__ == "__main__":
    setup_directories()
