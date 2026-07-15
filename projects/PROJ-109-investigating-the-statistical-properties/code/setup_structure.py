"""
Project Structure Setup Script.
Creates the required directory hierarchy for the llmXive pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base project root (assumed to be the directory containing this script's parent 'code')
    # The task requires paths relative to project root: code/, data/, tests/, results/
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        "code/data",
        "code/analysis",
        "data/raw",
        "data/processed",
        "results",
        "results/figures", # Subdirectory for T039
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
