import os
from pathlib import Path
from setup_directories import create_directory, main as setup_main


def main():
    """
    Create the results/models/ directory.
    This directory is used to store trained model artifacts (e.g., .pkl files).
    """
    root_dir = Path(__file__).resolve().parent.parent
    models_dir = root_dir / "results" / "models"
    
    create_directory(models_dir)
    print(f"Directory created: {models_dir}")


if __name__ == "__main__":
    main()