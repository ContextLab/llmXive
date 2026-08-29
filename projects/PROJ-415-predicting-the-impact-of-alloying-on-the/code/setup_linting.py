"""
Setup script for linting (Ruff) and formatting (Black) tools.
This script ensures configuration files are present in the project root.
"""
import os
import sys
from pathlib import Path

# Note: Configuration files (pyproject.toml, .pre-commit-config.yaml)
# are now managed as project artifacts. This script acts as a
# verification and installation helper.

def main():
    """
    Verifies the presence of linting configurations and provides installation instructions.
    """
    project_root = Path(__file__).resolve().parent.parent
    pyproject = project_root / "pyproject.toml"
    pre_commit = project_root / ".pre-commit-config.yaml"

    print("Checking linting and formatting configuration...")

    if not pyproject.exists():
        print("ERROR: pyproject.toml not found. Please ensure it exists with [tool.black] and [tool.ruff] sections.")
        sys.exit(1)

    if not pre_commit.exists():
        print("ERROR: .pre-commit-config.yaml not found. Please ensure it exists.")
        sys.exit(1)

    print("Configuration files found.")
    print("\nTo enable pre-commit hooks, run:")
    print("  pip install pre-commit black ruff")
    print("  pre-commit install")
    print("\nTo run linter manually:")
    print("  ruff check .")
    print("\nTo run formatter manually:")
    print("  black .")
    print("\nTo run both:")
    print("  pre-commit run --all-files")

if __name__ == "__main__":
    main()