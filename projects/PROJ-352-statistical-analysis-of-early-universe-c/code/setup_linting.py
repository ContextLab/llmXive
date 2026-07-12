"""
Setup script for linting and formatting tools.
Runs black, flake8, and pylint checks as a validation step.
"""
import subprocess
import sys
from pathlib import Path

from lint_config import check_black, check_flake8, check_pylint

def main():
    """Run linting and formatting checks."""
    project_root = Path(__file__).parent.parent
    print(f"Running linting checks in {project_root}...")

    # Run Black check
    print("\n--- Checking Black formatting ---")
    if not check_black(project_root):
        print("ERROR: Black formatting check failed.")
        return 1

    # Run Flake8 check
    print("\n--- Checking Flake8 linting ---")
    if not check_flake8(project_root):
        print("ERROR: Flake8 linting check failed.")
        return 1

    # Run Pylint check
    print("\n--- Checking Pylint ---")
    if not check_pylint(project_root):
        print("ERROR: Pylint check failed.")
        return 1

    print("\nAll linting checks passed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())