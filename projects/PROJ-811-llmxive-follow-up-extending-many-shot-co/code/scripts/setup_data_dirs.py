import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the project:
    - data/raw/
    - data/processed/
    - data/results/
    - artifacts/ (for checksums and state files)

    This script ensures idempotency by using os.makedirs with exist_ok=True.
    """
    # Determine project root based on script location
    # Assuming script is at code/scripts/setup_data_dirs.py
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    # Define relative paths as per task requirement
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "artifacts"
    ]

    created_count = 0
    for rel_path in data_dirs:
        full_path = project_root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())