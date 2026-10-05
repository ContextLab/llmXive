import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the llmXive project.
    Ensures all data, output, and metadata directories exist.
    """
    # Define the base project root (assuming this script is in code/)
    # We move up one level to get to the project root
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "distorted",
        project_root / "data" / "outputs",
        project_root / "data" / "metadata",
        project_root / "output" / "control",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())