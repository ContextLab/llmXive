import sys
from pathlib import Path
from config import ensure_directories

def main():
    """
    Entry point for setting up the data directory structure.
    Creates data/raw/, data/synthetic/, and data/processed/ directories.
    """
    print("Setting up data directory structure...")
    try:
        ensure_directories()
        print("Data directories created successfully.")
        return 0
    except Exception as e:
        print(f"Error creating data directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
