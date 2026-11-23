import os
import sys
from pathlib import Path

def create_project_structure(base_dir: Path) -> None:
    """
    Create the required data directory structure for the project.
    
    This function ensures the existence of the following directories:
    - data/raw
    - data/processed
    - data/aggregated
    
    Args:
        base_dir (Path): The base directory where the data folder will be created.
    """
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    aggregated_dir = data_dir / "aggregated"
    
    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    aggregated_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to ensure directories are tracked by git
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()
    (aggregated_dir / ".gitkeep").touch()
    
    # Log the created structure
    print(f"Created data directory structure at: {data_dir}")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    print(f"  - {aggregated_dir}")

def main() -> None:
    """
    Main entry point for creating the data directory structure.
    
    This script creates the required data directories under the project root.
    """
    # Determine the project root (parent of the code directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    create_project_structure(project_root)
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()