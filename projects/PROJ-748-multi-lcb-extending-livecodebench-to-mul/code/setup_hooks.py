"""
Script to install pre-commit hooks for the project.
Runs automatically after project setup or can be invoked manually.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """Install pre-commit hooks if pre-commit is available."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Check if pre-commit is installed
    try:
        subprocess.run(
            ["pre-commit", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: pre-commit is not installed. Please run: pip install pre-commit")
        print("Skipping hook installation.")
        return 0

    # Install the hooks
    print("Installing pre-commit hooks...")
    result = subprocess.run(
        ["pre-commit", "install"],
        check=True,
        capture_output=False,
        text=True,
    )

    if result.returncode == 0:
        print("Pre-commit hooks installed successfully.")
        print("Hooks will run automatically on 'git commit'.")
        print("To run manually: pre-commit run --all-files")
    else:
        print("Failed to install pre-commit hooks.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
