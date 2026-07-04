import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the llmXive pipeline.
    Ensures all necessary folders exist for data, source code, tests, and artifacts.
    """
    # Define the base directory (project root)
    # We assume the script runs from the project root or we derive it from __file__
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the directory structure relative to the project root
    # Based on tasks.md: `src/data`, `src/analysis`, `src/viz`, `tests/`, `data/`
    # The existing API surface suggests `code/` might be the root or `src/` is inside `code/`.
    # Looking at `code/src/config.py` in the API surface, the root seems to be `code/`.
    # So we create directories relative to `code/`.
    
    project_root = Path(__file__).resolve().parent
    
    directories = [
        "src/data",
        "src/analysis",
        "src/viz",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/figures",
        "data/logs",
        "specs",
        "contracts"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    create_directories()
