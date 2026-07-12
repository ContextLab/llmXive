import os
from pathlib import Path

def main():
    """
    Setup data directory structure for llmXive project.
    Creates the following directories relative to project root:
    - data/raw/
    - data/filtered/
    - data/scores/
    - outputs/
    """
    # Determine project root (assuming this script is in code/tools/)
    # We assume the script is run from the project root or we resolve relative to this file
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    data_dirs = [
        "data/raw",
        "data/filtered",
        "data/scores",
        "outputs"
    ]

    created = []
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it's a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")

    return 0

if __name__ == "__main__":
    exit(main())
