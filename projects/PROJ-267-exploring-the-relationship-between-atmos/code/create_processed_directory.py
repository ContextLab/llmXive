"""
Script to create the data/processed/ directory for the project.
"""
import os
from pathlib import Path

def ensure_processed_directory(root_path: Path) -> Path:
    """
    Ensure the 'data/processed' directory exists within the project root.

    Args:
        root_path: The project root directory path.

    Returns:
        The path to the created or existing 'data/processed' directory.
    """
    processed_dir = root_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def main():
    """
    Main entry point to create the processed directory.
    """
    # Determine project root based on script location
    # Assuming script is at code/create_processed_directory.py
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    processed_dir = ensure_processed_directory(project_root)
    print(f"Created/Verified directory: {processed_dir}")

if __name__ == "__main__":
    main()
