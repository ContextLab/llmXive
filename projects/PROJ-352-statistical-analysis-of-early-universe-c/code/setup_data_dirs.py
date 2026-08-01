import os
from pathlib import Path

def main():
    """
    Create the required data directory structure:
    - data/raw/
    - data/processed/
    - data/logs/
    
    This ensures the pipeline has a consistent file system layout.
    """
    base_dir = Path("data")
    
    # Define required directories
    directories = [
        base_dir / "raw",
        base_dir / "processed",
        base_dir / "logs",
        base_dir / "figures",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Data directory setup complete. {created_count} new directories created.")
    return 0
