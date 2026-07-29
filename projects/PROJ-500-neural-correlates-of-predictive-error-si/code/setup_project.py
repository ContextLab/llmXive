"""
Project setup script for initializing directory structure and configuration.

This script creates the necessary directory structure for the project
and initializes the configuration file.
"""

import os
from pathlib import Path


def main():
    """Initialize project directory structure."""
    # Define directories to create
    directories = [
        "src",
        "src/data",
        "src/utils",
        "src/analysis",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/interim",
        "data/processed",
        "logs",
        "analysis/results",
        "figures",
        "cache",
        "docs",
        "contracts",
    ]

    # Create directories
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

    # Create __init__.py files for Python packages
    init_files = [
        "src/__init__.py",
        "src/data/__init__.py",
        "src/utils/__init__.py",
        "src/analysis/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py",
    ]

    for init_file in init_files:
        path = Path(init_file)
        if not path.exists():
            path.touch()
            print(f"Created: {init_file}")

    print("\nProject structure initialized successfully!")
    print("Next steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Initialize git: git init")
    print("  3. Run tests: pytest")


if __name__ == "__main__":
    main()