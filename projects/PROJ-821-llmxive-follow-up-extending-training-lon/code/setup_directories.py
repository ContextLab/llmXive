import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory (parent of the 'code' directory)."""
    current_file = Path(__file__).resolve()
    # Assume code/ is directly under the project root
    return current_file.parent.parent

def create_directories() -> None:
    """Create all required project directories if they do not exist."""
    root = get_project_root()
    
    directories = [
        "code",
        "data",
        "data/synthetic",
        "data/synthetic/raw",
        "data/synthetic/short_context",
        "data/results",
        "data/results/logs",
        "data/results/aggregated",
        "tests",
        "models",
        "data/assets",
    ]
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified directory: {full_path}")

if __name__ == "__main__":
    create_directories()