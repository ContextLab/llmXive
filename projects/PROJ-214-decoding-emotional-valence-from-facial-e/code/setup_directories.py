"""
Directory structure setup for the DEAP EMG Valence Classification project.

This script creates the necessary directory structure for data storage:
- data/raw: Raw downloaded dataset files
- data/processed: Preprocessed feature data and logs
- data/models: Trained model artifacts and bundles
"""
import os
from pathlib import Path


def main():
    """Create the required directory structure at the project root."""
    # Determine project root (parent of the 'code' directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define required directories relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "data/models",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory setup complete. Created {created_count} new directories.")

    # Verify existence of all required directories
    all_exist = all((project_root / d).exists() for d in directories)
    if not all_exist:
        raise RuntimeError("Failed to create all required directories.")

    return 0


if __name__ == "__main__":
    exit(main())
