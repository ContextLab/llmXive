import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project data.
    This script ensures that 'data/raw' and 'data/derived' exist.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    derived_dir = data_dir / "derived"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)

    # Verify creation
    print(f"Created directory: {raw_dir}")
    print(f"Created directory: {derived_dir}")
    print(f"Directory structure verified: {raw_dir.exists()} and {derived_dir.exists()}")

if __name__ == "__main__":
    main()
