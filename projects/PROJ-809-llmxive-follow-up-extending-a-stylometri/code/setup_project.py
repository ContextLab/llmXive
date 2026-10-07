import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-809-llmxive-follow-up-extending-a-stylometri.
    Creates the required directory tree under the project root.
    """
    # Determine project root based on the script's location or environment
    # Assuming this script runs from the project root or is installed in the project
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-809-llmxive-follow-up-extending-a-stylometri"
    project_path = project_root / project_name

    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/hybrid",
        "artifacts/models",
        "artifacts/metrics",
        "contracts",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "state"
    ]

    print(f"Initializing project structure at: {project_path}")

    if not project_path.exists():
        project_path.mkdir(parents=True)
        print(f"Created project root: {project_path}")
    else:
        print(f"Project root already exists: {project_path}")

    for dir_name in directories:
        dir_path = project_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()