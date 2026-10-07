import os
import sys
from pathlib import Path

def setup_directories(project_root: Path) -> None:
    """
    Create the root project directories and all required subdirectories
    for the llmXive pipeline.

    Required structure:
    - code/
    - data/raw
    - data/processed
    - data/interim
    - data/results
    - state/
    - tests/unit
    - tests/integration
    - docs/
    """
    # Define all required directories relative to project_root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "state",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def main() -> None:
    """
    Entry point for the setup_directories script.
    Expects to be run from the project root or with a specified root.
    """
    # Determine project root: if running from code/, go up one level
    current_file = Path(__file__).resolve()
    if current_file.name == "setup_directories.py":
        # Assume script is in code/
        project_root = current_file.parent.parent
    else:
        project_root = current_file.parent

    print(f"Setting up directories for project: {project_root}")
    setup_directories(project_root)
    print("Directory setup complete.")

if __name__ == "__main__":
    main()