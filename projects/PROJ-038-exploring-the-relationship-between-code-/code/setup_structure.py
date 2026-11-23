"""
Project Structure Setup Script for llmXive Research Pipeline.

This script creates the required directory structure for the project,
ensuring all necessary folders exist for code, tests, and data management.

Directory Structure:
- code/
  - src/          (Source code modules)
  - tests/        (Test suites)
  - data/
    - raw/        (Raw ingested data)
    - processed/  (Processed/feature data)
    - results/    (Analysis results and reports)
"""

import os
import sys
from pathlib import Path


def create_directory_structure():
    """
    Create the standard project directory structure.

    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    base_path = Path("code")
    directories = [
        base_path,
        base_path / "src",
        base_path / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]

    created_count = 0
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created/Verified directory: {directory}")
        except OSError as e:
            print(f"Error creating directory {directory}: {e}", file=sys.stderr)
            return False

    print(f"\nSuccessfully created/verified {created_count} directories.")
    return True


def verify_structure():
    """
    Verify that the required directory structure exists.

    Returns:
        bool: True if all required directories exist, False otherwise.
    """
    required_dirs = [
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
    ]

    all_exist = True
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            print(f"Missing required directory: {dir_path}", file=sys.stderr)
            all_exist = False
        else:
            print(f"Verified directory: {dir_path}")

    return all_exist


def main():
    """
    Main entry point for the setup script.

    Creates the directory structure and verifies its existence.
    Exits with code 0 on success, 1 on failure.
    """
    print("Starting project structure setup...")
    print("-" * 40)

    if not create_directory_structure():
        print("Failed to create directory structure.", file=sys.stderr)
        sys.exit(1)

    print("-" * 40)
    print("Verifying directory structure...")
    if not verify_structure():
        print("Verification failed: Some directories are missing.", file=sys.stderr)
        sys.exit(1)

    print("-" * 40)
    print("Project structure setup completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()