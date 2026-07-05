import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'results' directory."""
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    create_directory(results_dir)
    print(f"Created directory: {results_dir}")

if __name__ == "__main__":
    main()
