import os
import sys
from pathlib import Path

def create_directories() -> None:
    """
    Create the project directory structure as specified in the implementation plan.
    
    Creates directories for source code, data storage (raw, processed, interim),
    testing suites, and documentation.
    """
    # Define the project root (assumed to be the parent of 'code' if running from there,
    # or the current working directory if 'code' is the root)
    # Based on the task description, paths are relative to the project root.
    # The existing API surface shows `code/setup_project.py`.
    # We need to create directories relative to the project root.
    # Assuming the script is run from the project root or 'code' directory.
    
    # Determine project root: If we are in code/, go up one level.
    current_file = Path(__file__).resolve()
    if current_file.parent.name == "code":
        project_root = current_file.parent.parent
    else:
        project_root = current_file.parent
    
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {full_path.relative_to(project_root)}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    create_directories()