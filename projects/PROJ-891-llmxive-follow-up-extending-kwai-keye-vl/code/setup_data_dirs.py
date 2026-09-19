"""
Setup script to create the required directory structure for the llmXive project.
Creates data directories: raw, distorted, outputs, metadata
Creates output directory: control
"""
import os
from pathlib import Path


def main():
    """Create the project's data and output directory structure."""
    # Define the base project root (assuming this script is in code/)
    # The directories should be created relative to the project root.
    # We assume the script is run from the project root or code/ directory.
    # To be safe, we determine the project root as the parent of 'code'.
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define required directories relative to project root
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "distorted",
        project_root / "data" / "outputs",
        project_root / "data" / "metadata",
        project_root / "output" / "control",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    print(f"Setup complete. Created {created_count} new directories.")
    return 0


if __name__ == "__main__":
    exit(main())