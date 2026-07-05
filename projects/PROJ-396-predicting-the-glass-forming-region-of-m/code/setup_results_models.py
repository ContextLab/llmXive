import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'results/models' directory."""
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    models_dir = results_dir / "models"
    create_directory(models_dir)
    print(f"Created directory: {models_dir}")

if __name__ == "__main__":
    main()
