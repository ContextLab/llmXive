"""
Project setup script for creating directory structure.
"""
import os
from pathlib import Path


def create_directories(base_path: str = ".") -> None:
    """
    Create the project directory structure.
    
    Args:
        base_path: Base directory path (default: current directory)
    """
    base = Path(base_path)
    
    # Define directory structure
    directories = [
        # Source directories
        "code/src/data",
        "code/src/models",
        "code/src/analysis",
        "code/src/cli",
        "code/src/lib",
        
        # Data directories
        "code/data/raw",
        "code/data/processed",
        
        # Results directory
        "code/results",
        
        # Test directories
        "code/tests/unit",
        "code/tests/integration",
        "code/tests/contract",
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")
    
    print("Directory structure created successfully.")


if __name__ == "__main__":
    create_directories()
