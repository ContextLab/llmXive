"""
Initialize project directory structure and __init__.py files.

This script creates the required directories and initializes Python packages
by creating empty __init__.py files in the appropriate locations.
"""
import os
from pathlib import Path


def main():
    """Create project structure."""
    # Define the root directory (current working directory)
    root = Path(".")

    # Define the directories to create based on tasks.md requirements
    # Note: 'src' and 'tests' are created with __init__.py, others are data/output dirs
    directories = [
        "src",
        "tests",
        "data",
        "figures",
        "logs",
        "report",
        "artifacts",
        # Subdirectories often needed for data organization
        "data/raw",
        "data/processed",
        "data/metadata",
    ]

    created_dirs = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    # Create __init__.py in src and tests
    init_files = [
        root / "src" / "__init__.py",
        root / "tests" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            # Create an empty __init__.py or with a docstring
            init_file.write_text(
                "# Auto-generated package initialization file.\n"
                "from . import utils  # Placeholder for future imports\n"
            )
            print(f"Created: {init_file}")
        else:
            print(f"File already exists: {init_file}")

    print("\nProject structure initialization complete.")


if __name__ == "__main__":
    main()
