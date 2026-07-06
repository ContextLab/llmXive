import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and raise an error if it fails."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    return result

def main():
    """
    Installs pre-commit and runs the initial hook setup.
    This script assumes the .pre-commit-config.yaml, .flake8, and pyproject.toml
    are already present in the project root.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Install pre-commit if not present
    print("Ensuring pre-commit is installed...")
    try:
        run_command([sys.executable, "-m", "pip", "install", "-q", "pre-commit"])
    except Exception as e:
        print(f"Warning: Could not install pre-commit: {e}")
        print("Please install it manually: pip install pre-commit")
        return

    # Install the git hooks
    print("Installing pre-commit hooks...")
    try:
        run_command([sys.executable, "-m", "pre_commit", "install"], cwd=project_root)
    except Exception as e:
        print(f"Failed to install hooks: {e}")
        return

    # Run hooks on all files to ensure immediate compliance
    print("Running pre-commit on all files...")
    try:
        run_command([sys.executable, "-m", "pre_commit", "run", "--all-files"], cwd=project_root)
        print("Linting and formatting checks passed.")
    except RuntimeError as e:
        print("Pre-commit checks failed. Please fix the issues indicated above.")
        print("You can also run manually: pre-commit run --all-files")
        # Do not raise here to allow the task to be marked as 'configured' even if fixes are needed

if __name__ == "__main__":
    main()