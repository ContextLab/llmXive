"""
Data Directory Setup Module.

This module provides functionality to create the required directory structure
for the project's data storage, ensuring that `raw/`, `processed/`, and
`contracts/` subdirectories exist under the `data/` root.
"""
import os
from pathlib import Path


def setup_data_directories(base_path: str = ".") -> None:
    """
    Create the standard data directory structure.

    Creates the following directories relative to `base_path`:
    - data/
    - data/raw/
    - data/processed/
    - data/contracts/

    Args:
        base_path: The root directory where the `data/` folder will be created.
                   Defaults to the current working directory.
    """
    base = Path(base_path)
    data_root = base / "data"
    directories = [
        data_root,
        data_root / "raw",
        data_root / "processed",
        data_root / "contracts",
    ]

    for directory in directories:
      if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        # Ensure the directory is accessible and created
        if not directory.exists():
          raise OSError(f"Failed to create directory: {directory}")

    # Verify creation
    for directory in directories:
      assert directory.exists(), f"Directory creation verification failed: {directory}"


if __name__ == "__main__":
    # Execute setup when run as a script
    setup_data_directories()
    print("Data directory structure created successfully.")
