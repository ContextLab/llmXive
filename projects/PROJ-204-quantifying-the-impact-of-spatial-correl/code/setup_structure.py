"""
Project structure setup module.
Creates the required directory hierarchy for the llmXive research pipeline.
"""
import os
from pathlib import Path


def create_project_structure() -> None:
    """
    Create the standard project directory structure required by the pipeline.
    
    Creates directories under the project root:
    - data/raw/
    - data/processed/
    - code/data/
    - code/preprocess/
    - code/analysis/
    - code/modeling/
    - code/validation/
    - code/report/
    - tests/ (includes unit/ and integration/ subdirectories)
    """
    # Define relative paths based on the task requirements
    # Note: The root is assumed to be the project root where this script is run
    # or where the project is initialized. We use Path.cwd() or a relative base.
    # To be safe for the pipeline context, we create relative to the script location
    # or the current working directory.
    
    base_path = Path.cwd()
    
    directories = [
        "data/raw",
        "data/processed",
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    print(f"Project structure setup complete. Created {created_count} new directories.")


if __name__ == "__main__":
    create_project_structure()