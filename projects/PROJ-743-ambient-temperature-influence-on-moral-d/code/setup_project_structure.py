import os
import sys
from pathlib import Path

def ensure_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    Directories created:
      - code/
      - data/raw/
      - data/processed/
      - results/figures/
      - results/logs/
      - results/stats/
      - tests/
    """
    # Define relative paths based on project root
    project_root = Path.cwd()
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/logs",
        "results/stats",
        "tests"
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

    print(f"Project structure setup complete. {created_count} new directories created.")
    return True

def main():
    """
    Entry point for the script.
    """
    success = ensure_directories()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()