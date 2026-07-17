"""
Script to initialize the data directory structure for the project.
Creates raw, processed, and consent directories as required by T005.
"""
import os
from pathlib import Path

# Import project root utilities from the existing config module
from config import get_project_root


def main():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/processed/
    - data/consent/
    """
    project_root = get_project_root()
    data_dir = project_root / "data"

    # Define required subdirectories
    subdirs = ["raw", "processed", "consent"]

    created_dirs = []
    for subdir_name in subdirs:
        dir_path = data_dir / subdir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    # Create a README in the consent directory to indicate it is empty
    # as per the project policy (no mock consent records for simulated data)
    consent_dir = data_dir / "consent"
    readme_path = consent_dir / ".gitkeep"
    if not readme_path.exists():
        with open(readme_path, "w") as f:
            f.write(
                "This directory is reserved for consent records.\n"
                "Per Constitution Principle VI, no mock consent records are generated\n"
                "for simulated studies. This directory remains empty.\n"
            )
        print(f"Created placeholder: {readme_path}")

    print("Data directory structure initialization complete.")
    return 0


if __name__ == "__main__":
    exit(main())