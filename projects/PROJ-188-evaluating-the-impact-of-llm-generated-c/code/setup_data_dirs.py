import os
from pathlib import Path

def create_data_directories():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/intermediate/
    - data/processed/

    This function is idempotent; it will not raise an error if directories
    already exist.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_root = base_dir / "data"
    
    directories = [
        data_root / "raw",
        data_root / "intermediate",
        data_root / "processed"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

if __name__ == "__main__":
    create_data_directories()
    print("Data directory structure setup complete.")