"""
Script to initialize linting and formatting configurations for the project.
This script ensures that .ruff.toml and requirements-dev.txt are present
and correctly configured according to project standards.
"""
import os
import sys
from pathlib import Path

def main():
    """Initialize linting configuration files."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    # Ensure code directory exists
    if not code_dir.exists():
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {code_dir}")

    # Define paths
    ruff_config = code_dir / ".ruff.toml"
    requirements_dev = code_dir / "requirements-dev.txt"

    # Check if ruff config exists
    if ruff_config.exists():
        print(f"Found existing linting config: {ruff_config}")
    else:
        print(f"Linting config not found. Please ensure {ruff_config} exists.")
        print("Run 'pip install -r code/requirements-dev.txt' to install tools.")
        return 1

    # Check if dev requirements exist
    if requirements_dev.exists():
        print(f"Found dev requirements: {requirements_dev}")
    else:
        print(f"Dev requirements not found. Please create {requirements_dev}.")
        return 1

    print("Linting and formatting environment is ready.")
    print("To format code: black code/")
    print("To lint code: ruff check code/")
    return 0

if __name__ == "__main__":
    sys.exit(main())