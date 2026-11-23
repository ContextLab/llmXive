"""
Script to initialize and verify linting (ruff) and formatting (black) tools.
This script ensures the project is configured for consistent code style.
"""
import subprocess
import sys
from pathlib import Path
from config import get_project_root
from config_linting import main as config_linting_main
from linting_setup import main as linting_setup_main


def main():
    """
    Entry point to configure and verify ruff and black.
    """
    print("Initializing Linting and Formatting configuration...")

    project_root = get_project_root()
    print(f"Project root detected at: {project_root}")

    # 1. Ensure configuration files (pyproject.toml) exist and are valid
    # This is handled by the project setup, but we verify the tool presence here.
    config_linting_main()

    # 2. Verify tools are installed
    linting_setup_main()

    print("Linting (ruff) and Formatting (black) configuration complete.")
    print("Run 'ruff check .' to lint and 'black .' to format.")


if __name__ == "__main__":
    main()
