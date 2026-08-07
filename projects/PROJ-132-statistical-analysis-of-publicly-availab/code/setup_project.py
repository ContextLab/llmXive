"""
Project Setup Script for llmXive Automated Science Pipeline.
This script creates the required directory structure for the project.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """
    Create the project directory structure as per the implementation plan.
    Creates:
    - src/data, src/models, src/analysis
    - data/raw, data/processed, data/interim
    - tests/contract, tests/unit, tests/integration
    - docs
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the directories to create relative to the project root
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        # Additional provenance directory often needed for downstream tasks
        "data/provenance",
        # Logs directory for pipeline execution
        "logs",
    ]

    created_count = 0
    skipped_count = 0

    print(f"Creating project structure in: {base_dir}")

    for dir_path_str in directories:
        dir_path = base_dir / dir_path_str
        if dir_path.exists():
            skipped_count += 1
            print(f"  [SKIP] {dir_path} (already exists)")
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"  [CREATED] {dir_path}")

    print(f"\nSetup complete. Created: {created_count}, Skipped: {skipped_count}")
    return True


def main():
    """Entry point for the script."""
    try:
        create_directories()
        print("Project structure verification successful.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during project setup: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()