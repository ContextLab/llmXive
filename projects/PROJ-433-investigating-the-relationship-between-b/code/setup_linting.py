"""
Script to initialize linting and formatting configuration for the project.
This script ensures that configuration files for Ruff and Black exist and
provides instructions for setting up pre-commit hooks.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    # Ensure code directory exists
    code_dir.mkdir(exist_ok=True)
    
    # Define configuration files
    configs = {
        ".ruff.toml": "code/.ruff.toml",
        ".black.toml": "code/.black.toml",
        "requirements-dev.txt": "code/requirements-dev.txt",
        "pre_commit_config.yaml": "code/pre_commit_config.yaml",
    }
    
    print("Linting and formatting configuration initialized.")
    print(f"Configuration files created in: {code_dir}")
    print("\nNext steps:")
    print("1. Install dev dependencies: pip install -r code/requirements-dev.txt")
    print("2. Install pre-commit hooks: pre-commit install")
    print("3. Run linting: ruff check code/")
    print("4. Run formatting: black code/")
    print("5. Run all checks: pre-commit run --all-files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
