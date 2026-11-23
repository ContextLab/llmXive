import os
from pathlib import Path
from typing import List

def create_structure() -> List[str]:
    """
    Creates the required project directory structure for the solar irradiance
    reconstruction pipeline.

    Creates:
      - code/
      - code/models/
      - code/models/artifacts/
      - code/analysis/
      - code/data/
      - tests/
      - data/raw/
      - data/processed/

    Returns:
        List[str]: List of created directory paths.
    """
    base_dir = Path(".")
    directories = [
        base_dir / "code",
        base_dir / "code" / "models",
        base_dir / "code" / "models" / "artifacts",
        base_dir / "code" / "analysis",
        base_dir / "code" / "data",
        base_dir / "tests",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
    ]

    created_paths = []
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(directory))

    return created_paths

def main():
    """Entry point for directory structure creation."""
    print("Creating project directory structure...")
    paths = create_structure()
    for path in paths:
        print(f"  Created: {path}")
    print("Directory structure creation complete.")

if __name__ == "__main__":
    main()
