import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the data/processed/ directory at the project root."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    processed_dir = data_dir / "processed"
    
    if create_directory(processed_dir):
        print(f"Successfully created directory: {processed_dir}")
        return True
    else:
        print(f"Directory already exists or failed to create: {processed_dir}")
        return True  # Idempotent: success if it already exists

if __name__ == "__main__":
    main()
