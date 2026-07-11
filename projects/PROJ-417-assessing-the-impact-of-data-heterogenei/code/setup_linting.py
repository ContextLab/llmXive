"""
Setup script to initialize pre-commit hooks and verify linting configuration.
This script ensures that flake8, black, and pre-commit are installed and
that the configuration files are correctly placed.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def main():
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print(f"Project root: {project_root}")

    # Check if configuration files exist
    config_files = [
        ".flake8",
        "pyproject.toml",
        ".pre-commit-config.yaml",
        "requirements.txt"
    ]

    for config_file in config_files:
        if not (project_root / config_file).exists():
            print(f"Error: {config_file} not found in project root.")
            return 1

    # Install pre-commit if not present
    print("\n--- Installing pre-commit if needed ---")
    run_command(
        [sys.executable, "-m", "pip", "install", "pre-commit"],
        "Installing pre-commit"
    )

    # Install/upgrade linting tools
    print("\n--- Installing linting tools ---")
    run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "Installing requirements (including flake8, black, pre-commit)"
    )

    # Initialize pre-commit
    print("\n--- Initializing pre-commit hooks ---")
    if not run_command(
        ["pre-commit", "install"],
        "Installing pre-commit hooks"
    ):
        print("Warning: pre-commit install failed. You may need to run 'pre-commit install' manually.")

    print("\n--- Linting configuration complete ---")
    print("To run linting manually: pre-commit run --all-files")
    print("To run flake8: flake8 code/")
    print("To run black: black code/")

    return 0

if __name__ == "__main__":
    sys.exit(main())