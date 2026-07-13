"""
Script to initialize the project's data and state directory structures.
Creates required subdirectories for raw data, processed data, model outputs,
and artifact hash storage.
"""
import os
from pathlib import Path

# Define the project root relative to this script's location
# Assuming this script is in code/ and we need to go up one level
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define the directories to create
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"
REPORTS_DIR = DATA_DIR / "reports"

STATE_DIR = PROJECT_ROOT / "state"
ANALYSIS_DIR = DATA_DIR / "analysis"
FIGURES_DIR = DATA_DIR / "figures"

def main():
    """Create the directory structure if it doesn't exist."""
    directories = [
        RAW_DIR,
        PROCESSED_DIR,
        MODELS_DIR,
        REPORTS_DIR,
        ANALYSIS_DIR,
        FIGURES_DIR,
        STATE_DIR,
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    # Create .gitkeep files to ensure directories are tracked by git
    keep_file_content = "# This file ensures the directory is tracked by version control.\n"
    for dir_path in directories:
        keep_file = dir_path / ".gitkeep"
        with open(keep_file, "w", encoding="utf-8") as f:
            f.write(keep_file_content)
        
    print(f"\nDirectory structure initialization complete. Created {created_count} new directories.")
    print(f"Data root: {DATA_DIR}")
    print(f"State root: {STATE_DIR}")

if __name__ == "__main__":
    main()
