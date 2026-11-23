"""
Script to create the required data directory structure for the bias detection pipeline.

This script ensures the existence of:
- data/raw: For raw input data (repositories, lexicons, validation datasets)
- data/processed: For intermediate and final processed artifacts
- data/validation: For manually labeled validation datasets

Usage:
    python code/setup_data_dirs.py
"""
import os
from pathlib import Path

def create_data_directories(root_dir: str = ".") -> None:
    """
    Create the data directory structure relative to the project root.
    
    Args:
        root_dir: The project root directory (default: current directory)
    
    Raises:
        OSError: If directory creation fails
    """
    root_path = Path(root_dir)
    
    # Define the required directories
    data_dirs = [
        root_path / "data" / "raw",
        root_path / "data" / "processed",
        root_path / "data" / "validation",
    ]
    
    created_count = 0
    for dir_path in data_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Data directory setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    create_data_directories()
