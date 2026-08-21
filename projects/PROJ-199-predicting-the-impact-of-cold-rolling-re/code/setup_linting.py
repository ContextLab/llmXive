"""
Setup script to install and configure linting tools (flake8, black, isort, pre-commit).
This script ensures the project adheres to the agreed-upon code style and quality standards.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command: list, description: str) -> bool:
    """
    Run a shell command and print status.
    Returns True if successful, False otherwise.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print(f"Success: {description}\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed: {description}")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Failed: {description} - Command not found.")
        return False

def main():
    """
    Main entry point for setting up linting infrastructure.
    """
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root detected at: {project_root}\n")

    # 1. Install pre-commit
    print("--- Installing pre-commit ---")
    success = run_command([sys.executable, "-m", "pip", "install", "pre-commit"], "Installing pre-commit")
    if not success:
        print("Could not install pre-commit. Exiting.")
        sys.exit(1)

    # 2. Install development dependencies (black, flake8, isort) if not already present
    # Note: requirements.txt should ideally contain these, but we ensure them here for robustness.
    dev_deps = ["black", "flake8", "isort"]
    for dep in dev_deps:
        print(f"--- Ensuring {dep} is installed ---")
        run_command([sys.executable, "-m", "pip", "install", dep], f"Installing {dep}")

    # 3. Initialize pre-commit hooks
    print("--- Initializing pre-commit hooks ---")
    success = run_command(["pre-commit", "install"], "Installing pre-commit git hooks")
    if not success:
        print("Warning: Could not install pre-commit git hooks. You may need to run 'pre-commit install' manually.")

    # 4. Run a dry-run of pre-commit on the codebase to verify configuration
    print("\n--- Verifying configuration with pre-commit (dry run) ---")
    # We run on the current directory, but exclude data/docs to avoid heavy processing
    success = run_command(
        ["pre-commit", "run", "--all-files"],
        "Running pre-commit checks on all files"
    )

    if success:
        print("\n✅ Linting setup complete. All checks passed.")
    else:
        print("\n⚠️  Linting setup complete, but some checks failed. Please review the output above.")
        print("You can run 'pre-commit run --all-files' manually to fix issues.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())