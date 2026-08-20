"""
Verify Setup Script for llmXive Cortical Column Project.

This script validates that all directories created in T001a, T001b, T001c
exist and that the state template file `state/template.yaml` is present.

Exit codes:
  0: All checks passed.
  1: One or more checks failed (missing directories or files).
"""
import os
import sys
from pathlib import Path

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories required by T001a, T001b, T001c
REQUIRED_DIRS = [
    # From T001a: src/
    "src",
    # From T001b: models, data, training, experiments, utils (inside src/)
    "src/models",
    "src/data",
    "src/training",
    "src/experiments",
    "src/utils",
    # From T001c: tests/unit, tests/integration, scripts, data/results, data/logs, data/configs, state/
    "tests/unit",
    "tests/integration",
    "scripts",
    "data/results",
    "data/logs",
    "data/configs",
    "state",
]

# Required file: state/template.yaml
REQUIRED_FILES = [
    "state/template.yaml",
]

def verify_setup() -> bool:
    """
    Verify all required directories and files exist.

    Returns:
        True if all checks pass, False otherwise.
    """
    all_passed = True

    print(f"Verifying setup for project at: {PROJECT_ROOT}")
    print("-" * 60)

    # Check directories
    print("Checking directories...")
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path} (Missing or not a directory)")
            all_passed = False

    # Check files
    print("\nChecking files...")
    for file_path in REQUIRED_FILES:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists() and full_path.is_file():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [FAIL] {file_path} (Missing or not a file)")
            all_passed = False

    print("-" * 60)
    if all_passed:
        print("Setup verification: PASSED")
    else:
        print("Setup verification: FAILED")

    return all_passed

def main():
    """Main entry point for the script."""
    success = verify_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()