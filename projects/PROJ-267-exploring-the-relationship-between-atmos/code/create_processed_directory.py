import os
from pathlib import Path

def ensure_processed_directory():
    """
    Creates the 'data/processed' directory if it does not exist.
    Returns the Path object of the created directory.
    """
    # Determine project root relative to this script's location
    # Assuming script is in code/, root is parent of code/
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"

    if not processed_dir.exists():
        processed_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {processed_dir}")
    else:
        print(f"Directory already exists: {processed_dir}")

    return processed_dir

def main():
    ensure_processed_directory()

if __name__ == "__main__":
    main()