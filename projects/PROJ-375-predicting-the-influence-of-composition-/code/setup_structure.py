import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    This function is idempotent.
    """
    root = Path(__file__).resolve().parent.parent
    
    directories = [
        # Setup Phase (T001, T001a, T001b, T001c)
        "code/ingestion",
        "code/features",
        "code/modeling",
        "code/utils",
        "code/models",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs",
        "results",
        
        # Additional standard directories
        "logs",
        "contracts",
        "figures",
    ]
    
    for dir_name in directories:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")

if __name__ == "__main__":
    create_directories()