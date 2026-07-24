"""
Script to create the required data directory structure for the project.
Creates data/raw/, data/intermediate/, and data/processed/ directories.
"""
import os
from pathlib import Path


def create_data_directories():
    """
    Creates the standard data directory structure required by the project.
    Directories created:
        - data/raw/
        - data/intermediate/
        - data/processed/
    
    Returns:
        None
    
    Raises:
        OSError: If directory creation fails due to permissions or other OS errors.
    """
    base_dir = Path("data")
    
    directories = [
        base_dir / "raw",
        base_dir / "intermediate",
        base_dir / "processed",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    print("Data directory structure setup complete.")


if __name__ == "__main__":
    create_data_directories()