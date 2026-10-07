"""
Project setup script for llmXive COVID-19 Vaccine Adverse Event Analysis.
Creates the required directory structure as specified in T001a.
"""
import os
from pathlib import Path


def create_directories():
    """
    Create the project directory structure.
    Creates: src/, tests/, data/, data/raw/, data/processed/, output/, contracts/, logs/
    """
    # Define the project root (current directory where script is run)
    project_root = Path(__file__).parent.resolve()

    # Define all required directories relative to the project root
    # Based on tasks.md: T001a requires src/, tests/, data/, data/raw/, data/processed/, output/, contracts/, logs/
    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "output",
        "contracts",
        "logs",
    ]

    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise NotADirectoryError(
                    f"Path exists but is not a directory: {full_path}"
                )

    return created_dirs


if __name__ == "__main__":
    print("Setting up project directory structure...")
    created = create_directories()
    if created:
        print(f"Created directories: {created}")
    else:
        print("All required directories already exist.")
    print("Project structure setup complete.")
