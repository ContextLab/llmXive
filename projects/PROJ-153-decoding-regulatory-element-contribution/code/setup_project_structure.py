import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the standard project directory structure for the llmXive pipeline.
    Directories created:
        - code/
        - tests/
        - data/raw/
        - data/processed/
        - results/
        - figures/
        - logs/
    """
    base_dir = Path(__file__).resolve().parent.parent
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/external",
        "results",
        "figures",
        "logs",
        "specs"
    ]

    created_count = 0
    for dir_name in directories:
        target_path = base_dir / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")

    if created_count == 0:
        print("No new directories created. All required directories exist.")
    else:
        print(f"Successfully created {created_count} directory structure(s).")

    return True

def main():
    """Entry point for the script."""
    try:
        create_directories()
        return 0
    except Exception as e:
        print(f"Error creating project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
