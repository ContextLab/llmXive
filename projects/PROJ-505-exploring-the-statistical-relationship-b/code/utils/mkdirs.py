"""
Utility script to ensure all required project directories exist.
This script is idempotent and safe to run multiple times.
"""
import os
from pathlib import Path

def ensure_dirs(base_path: str) -> None:
    """
    Creates the directory structure for the project if it doesn't exist.
    
    Args:
        base_path: The root path of the project.
    """
    project_root = Path(base_path)
    
    # Define all required directories relative to the project root
    directories = [
        "code",
        "code/ingestion",
        "code/analysis",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/artifacts",  # The specific target for T010
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory: {full_path}")

if __name__ == "__main__":
    # Determine the project root based on the current file location
    # This script is located at code/utils/mkdirs.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    ensure_dirs(project_root)
    print("All directories ensured.")