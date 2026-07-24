"""
Setup script to create the required directory structure for the llmXive project.
Creates the `code/` directory and its subdirectories as specified in T001a.
"""
import os
from pathlib import Path

def create_directories():
    """
    Creates the directory structure:
    code/
    ├── data_generation
    ├── model_training
    ├── simulation
    ├── analysis
    └── tests
    """
    base_dir = Path("code")
    subdirs = [
        "data_generation",
        "model_training",
        "simulation",
        "analysis",
        "tests"
    ]

    created_paths = []
    for subdir in subdirs:
        path = base_dir / subdir
        path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(path))
        print(f"Created directory: {path}")

    return created_paths

def main():
    """Entry point for the script."""
    print("Setting up code directory structure...")
    paths = create_directories()
    print(f"Successfully created {len(paths)} directories.")
    return 0

if __name__ == "__main__":
    exit(main())