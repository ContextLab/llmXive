import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'results/validation' directory."""
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    validation_dir = results_dir / "validation"
    create_directory(validation_dir)
    print(f"Created directory: {validation_dir}")

if __name__ == "__main__":
    main()
