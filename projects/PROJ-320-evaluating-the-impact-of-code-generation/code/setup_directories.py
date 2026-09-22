"""
Script to create the required project directory structure.

This script ensures all necessary directories and __init__.py files
exist for the llm-code-review-impact pipeline.
"""

import os
from pathlib import Path


def create_directories():
    """Create all required project directories and __init__.py files."""
    base_path = Path(__file__).parent.parent

    # Define directory structures
    directories = [
        "code",
        "code/data",
        "code/analysis",
        "code/audit",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "reports/figures",
    ]

    # Define __init__.py locations
    init_files = [
        "code/__init__.py",
        "code/data/__init__.py",
        "code/analysis/__init__.py",
        "code/audit/__init__.py",
        "code/utils/__init__.py",
        "data/raw/__init__.py",
        "data/processed/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "reports/figures/__init__.py",
    ]

    # Create directories
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create __init__.py files if they don't exist
    for init_path in init_files:
        full_path = base_path / init_path
        if not full_path.exists():
            full_path.touch()
            print(f"Created __init__.py: {full_path}")
        else:
            print(f"__init__.py already exists: {full_path}")


def main():
    """Entry point for directory setup."""
    print("Setting up project directories...")
    create_directories()
    print("Project directory structure setup complete.")


if __name__ == "__main__":
    main()