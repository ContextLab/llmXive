"""
Data directory structure setup for the Socratic Transformers project.

This module creates the required directory structure for raw, processed,
and result data, along with .gitkeep files to ensure directories are
tracked by version control.
"""
import os
import sys
from pathlib import Path


def create_gitkeep(directory: Path) -> None:
    """
    Create a .gitkeep file in the specified directory.
    
    Args:
        directory: Path to the directory where .gitkeep should be created.
    """
    gitkeep_path = directory / ".gitkeep"
    gitkeep_path.touch()
    print(f"Created .gitkeep in: {gitkeep_path}")


def setup_data_directories(base_path: Path) -> None:
    """
    Create the standard data directory structure.
    
    Args:
        base_path: Base path where the data directory will be created.
    """
    data_root = base_path / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    results_dir = data_root / "results"
    
    # Create directories
    for dir_path in [data_root, raw_dir, processed_dir, results_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create .gitkeep files
    for dir_path in [data_root, raw_dir, processed_dir, results_dir]:
        create_gitkeep(dir_path)


def main() -> int:
    """
    Main entry point for the data setup script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Determine the base path (project root)
        # The script is expected to be run from the project root
        base_path = Path.cwd()
        
        print(f"Setting up data directories in: {base_path}")
        setup_data_directories(base_path)
        
        print("\nData directory structure setup complete!")
        print(f"  - {base_path}/data/raw/")
        print(f"  - {base_path}/data/processed/")
        print(f"  - {base_path}/data/results/")
        
        return 0
    except Exception as e:
        print(f"Error setting up data directories: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
