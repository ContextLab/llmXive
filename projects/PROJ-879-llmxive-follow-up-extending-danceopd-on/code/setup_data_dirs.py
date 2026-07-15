import os
import sys
from pathlib import Path


def main():
    """
    Setup data directories for the llmXive project.
    Creates:
      - data/raw/
      - data/processed/
      - data/results/
    relative to the project root.
    """
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define relative paths for data directories
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
    ]

    created_dirs = []
    for rel_path in data_dirs:
        full_path = project_root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_dirs.append(full_path)
        else:
            print(f"Directory already exists: {full_path}")

    if not created_dirs:
        print("All required data directories already exist.")
    else:
        print(f"Successfully created {len(created_dirs)} directory/directories.")

    # Verify existence
    missing = [d for d in data_dirs if not (project_root / d).exists()]
    if missing:
        print(f"ERROR: The following directories were not created: {missing}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Verification successful: All data directories exist.")


if __name__ == "__main__":
    main()