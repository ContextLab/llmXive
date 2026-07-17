import os
from pathlib import Path
from code.config import (
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_RESULTS_DIR,
)


def setup_directories() -> None:
    """
    Create the required directory structure for data storage.

    Creates:
    - data/raw/: for original downloaded datasets
    - data/processed/: for intermediate feature matrices
    - data/results/: for analysis outputs and reports
    """
    directories = [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR]

    for dir_path in directories:
        path_obj = Path(dir_path)
        path_obj.mkdir(parents=True, exist_ok=True)
        # Ensure the directory is actually created (fail loudly if permissions issue)
        if not path_obj.exists():
            raise RuntimeError(f"Failed to create directory: {path_path}")


def main() -> None:
    """Entry point for directory setup script."""
    print("Setting up project directory structure...")
    setup_directories()
    print(f"Created: {DATA_RAW_DIR}")
    print(f"Created: {DATA_PROCESSED_DIR}")
    print(f"Created: {DATA_RESULTS_DIR}")
    print("Directory setup complete.")


if __name__ == "__main__":
    main()
