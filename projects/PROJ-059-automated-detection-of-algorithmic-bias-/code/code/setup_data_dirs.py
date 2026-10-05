"""
Script to create the required data directory structure for the project.
Implements Task T006: Create `data/` directory structure.
"""
import os
from pathlib import Path

def create_data_directories():
    """
    Creates the directory structure for raw, processed, and validation data.
    Ensures all directories exist relative to the project root.
    """
    # Determine the project root (assuming this script is in code/ or code/scripts/)
    # We use the parent of the current file's directory to find 'code/', then go up to root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent 

    data_base = project_root / "data"
    directories = [
        data_base / "raw",
        data_base / "processed",
        data_base / "validation"
    ]

    created = []
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(str(directory.relative_to(project_root)))
        print(f"Created/Verified directory: {directory}")

    print(f"\nData directory structure created successfully under: {data_base}")
    return created

if __name__ == "__main__":
    create_data_directories()