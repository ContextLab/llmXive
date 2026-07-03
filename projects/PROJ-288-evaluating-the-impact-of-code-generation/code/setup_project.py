"""
Project Setup Script for llmXive: Evaluating the Impact of Code Generation.

This script initializes the project directory structure as defined in the 
implementation plan (FR-001, FR-002).

It creates the necessary directories for code, data, tests, and documentation.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to the script location or current working directory
    # We assume the script is run from the project root or we determine the root dynamically
    # For robustness, we'll use the current working directory as the project root
    project_root = Path.cwd()

    # Define the directory structure to create
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
    existing_count = 0

    print(f"Setting up project structure in: {project_root}")

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.exists():
                if any(full_path.iterdir()):
                    print(f"  [INFO] Directory exists and is not empty: {dir_path}")
                    existing_count += 1
                else:
                    print(f"  [OK] Created directory: {dir_path}")
                    created_count += 1
            else:
                # Should not happen if exist_ok=True, but for safety
                print(f"  [ERROR] Failed to create: {dir_path}")
        except PermissionError:
            print(f"  [ERROR] Permission denied creating: {dir_path}")
            return 1
        except Exception as e:
            print(f"  [ERROR] Unexpected error creating {dir_path}: {e}")
            return 1

    print(f"\nSetup complete.")
    print(f"  New directories created: {created_count}")
    print(f"  Existing directories found: {existing_count}")

    # Create __init__.py files to ensure Python packages are recognized
    package_dirs = [
        "code",
        "code/data",
        "code/analysis",
        "tests",
        "tests/unit",
        "tests/integration"
    ]

    for pkg_dir in package_dirs:
        init_file = project_root / pkg_dir / "__init__.py"
        if not init_file.exists():
            try:
                init_file.touch()
                print(f"  [OK] Created package init: {pkg_dir}/__init__.py")
            except Exception as e:
                print(f"  [WARN] Could not create init file for {pkg_dir}: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
