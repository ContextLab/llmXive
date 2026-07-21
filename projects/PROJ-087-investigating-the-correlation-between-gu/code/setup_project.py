"""
Project structure initialization script.
Creates the required directory tree and __init__.py files as per the implementation plan.
"""
import os
from pathlib import Path


def main():
    """Create the project directory structure and init files."""
    # Define the root directory (current working directory or explicit path)
    root = Path(__file__).resolve().parent

    # Define the required directories relative to the root
    # Based on T001: src, data/raw, data/processed, tests/unit, tests/integration, docs
    directories = [
        "src",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    created_dirs = []
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
        print(f"Created directory: {full_path}")

    # Define __init__.py locations
    # Based on T001: create empty __init__.py in src, tests, tests/unit, tests/integration
    init_paths = [
        root / "src" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "tests" / "unit" / "__init__.py",
        root / "tests" / "integration" / "__init__.py",
    ]

    for init_path in init_paths:
        # Ensure parent directory exists before creating file
        init_path.parent.mkdir(parents=True, exist_ok=True)
        if not init_path.exists():
            init_path.touch()
            print(f"Created file: {init_path}")
        else:
            print(f"File already exists: {init_path}")

    print("Project structure initialization complete.")


if __name__ == "__main__":
    main()