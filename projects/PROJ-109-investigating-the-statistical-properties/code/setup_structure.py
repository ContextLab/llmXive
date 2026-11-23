"""
T001: Create project structure per implementation plan.

This script creates the required directory structure for the llmXive
automated science pipeline. It ensures all necessary folders exist
under the project root.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the project root (current directory where script is run)
    project_root = Path.cwd()

    # Define the required directories relative to project root
    directories = [
        "code/data",
        "code/analysis",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1

    print(f"\nSetup complete: {created_count} directories created, {existing_count} already existed.")
    print(f"Project root: {project_root}")

    # Verify structure by listing created dirs
    print("\nVerifying structure:")
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path} - NOT FOUND")
            sys.exit(1)

if __name__ == "__main__":
    main()