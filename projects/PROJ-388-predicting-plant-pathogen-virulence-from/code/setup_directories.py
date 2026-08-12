import os
from pathlib import Path

def create_directories():
    """
    Configure directory structure for the project:
    - data/raw
    - data/processed
    - output
    - src/data
    - src/analysis
    - src/viz
    
    Creates all necessary directories if they do not exist.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "output",
        base_dir / "src" / "data",
        base_dir / "src" / "analysis",
        base_dir / "src" / "viz",
    ]
    
    created = []
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(str(directory))
        print(f"Created directory: {directory}")
    
    return created

if __name__ == "__main__":
    create_directories()