"""
Project setup script for llmXive automated science pipeline.
Creates the required directory structure and initializes empty files.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the root directory (project root)
    root = Path(".")

    # Define the directories to create based on tasks.md
    directories = [
        "code",
        "data",
        "results",
        "tests",
        "docs"
    ]

    # Create directories
    for dir_name in directories:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create subdirectories for data organization
    data_subdirs = [
        "data/raw",
        "data/processed",
        "data/checksums"
    ]
    for dir_name in data_subdirs:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create results subdirectories
    results_subdirs = [
        "results/models",
        "results/models/ensemble",
        "results/models/mc_dropout"
    ]
    for dir_name in results_subdirs:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create tests subdirectories
    tests_subdirs = [
        "tests/unit",
        "tests/contract",
        "tests/integration"
    ]
    for dir_name in tests_subdirs:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create docs subdirectories
    docs_subdirs = [
        "docs/api",
        "docs/specs"
    ]
    for dir_name in docs_subdirs:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create logs directory
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {logs_dir}")

    print("Project directory structure created successfully.")

if __name__ == "__main__":
    main()