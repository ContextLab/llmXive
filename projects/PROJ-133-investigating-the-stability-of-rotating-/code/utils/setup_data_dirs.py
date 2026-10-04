import os
import sys
from pathlib import Path

def create_project_structure(base_dir: str = "data") -> None:
    """
    Create the required data directory structure for the project.
    
    Creates the following hierarchy relative to base_dir:
    - raw/
    - processed/
    - aggregated/
    
    Args:
        base_dir: The root directory where the data folders will be created.
                 Defaults to "data" relative to the project root.
    """
    data_path = Path(base_dir)
    
    # Define the required subdirectories
    subdirs = [
        data_path / "raw",
        data_path / "processed",
        data_path / "aggregated"
    ]
    
    # Create directories if they don't exist
    created = []
    for subdir in subdirs:
        if not subdir.exists():
            subdir.mkdir(parents=True, exist_ok=True)
            created.append(str(subdir))
            print(f"Created directory: {subdir}")
        else:
            print(f"Directory already exists: {subdir}")
    
    if not created:
        print("All required data directories already exist.")
    else:
        print(f"\nSuccessfully created {len(created)} directory/directories.")

def main() -> None:
    """Entry point for the script."""
    # Determine the project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    data_root = project_root / "data"
    
    print(f"Setting up data directories under: {data_root}")
    create_project_structure(str(data_root))

if __name__ == "__main__":
    main()
