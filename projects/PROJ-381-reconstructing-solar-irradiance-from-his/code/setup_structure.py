import os
from pathlib import Path
from typing import List

def create_structure(base_path: Path) -> None:
    """
    Create the project directory structure for the Solar Irradiance Reconstruction project.
    
    Creates the following directories relative to base_path:
    - code/
    - code/models/
    - code/analysis/
    - code/data/
    - tests/
    - data/raw/
    - data/processed/
    """
    # Define all required directories
    directories: List[Path] = [
        base_path / "code",
        base_path / "code" / "models",
        base_path / "code" / "analysis",
        base_path / "code" / "data",
        base_path / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
    ]
    
    # Create each directory (parents=True ensures intermediate dirs are created)
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def main() -> None:
    """Main entry point to create the project structure."""
    base_path = Path(__file__).parent.parent
    create_structure(base_path)
    print("Project structure created successfully.")

if __name__ == "__main__":
    main()
