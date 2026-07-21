"""
Project Setup Script for llmXive - Evaluating the Impact of Code Generation

This script creates the necessary directory structure for the research project
as defined in the implementation plan (FR-001, FR-002).
"""
import os
import sys
from pathlib import Path


def main():
    """
    Create the project directory structure.

    Creates the following directories relative to the project root:
    - code/data
    - code/analysis
    - data/raw
    - data/processed
    - data/baseline_corpus
    - tests/unit
    - tests/integration
    - docs/reports
    """
    # Define the base path (project root)
    # We assume this script is run from the project root or code/ directory
    # If run from code/, we need to go up one level
    current_file = Path(__file__).resolve()
    if current_file.parent.name == 'code':
        project_root = current_file.parent.parent
    else:
        project_root = current_file.parent

    # Define the directories to create
    directories = [
        "code/data",
        "code/analysis",
        "data/raw",
        "data/processed",
        "data/baseline_corpus",
        "tests/unit",
        "tests/integration",
        "docs/reports"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Setting up project structure in: {project_root}")

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            # exist_ok=True ensures we don't error if the directory already exists
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                print(f"  ✓ Created/Verified: {dir_path}")
                created_count += 1
            else:
                print(f"  ✗ Failed to create: {dir_path} (file exists with same name)")
        except PermissionError:
            print(f"  ✗ Permission denied: {dir_path}")
        except Exception as e:
            print(f"  ✗ Error creating {dir_path}: {e}")

    print(f"\nSetup complete: {created_count} directories ready, {skipped_count} skipped.")

    # Verification: List the created structure
    print("\nProject Structure Verification:")
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [MISSING] {dir_path}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
