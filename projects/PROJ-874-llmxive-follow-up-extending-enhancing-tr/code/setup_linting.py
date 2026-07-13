"""
Script to initialize linting and formatting configuration for the project.
This script ensures that ruff and black configurations are present and valid.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Stderr: {e.stderr}")
        return False

def main():
    root_dir = Path(__file__).parent.parent
    print(f"Project root: {root_dir}")

    # Check if ruff is installed
    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
        print("Ruff is installed.")
    except subprocess.CalledProcessError:
        print("Installing ruff...")
        subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True)

    # Check if black is installed
    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
        print("Black is installed.")
    except subprocess.CalledProcessError:
        print("Installing black...")
        subprocess.run([sys.executable, "-m", "pip", "install", "black"], check=True)

    # Run initial lint check
    print("\n--- Running initial lint check ---")
    success = run_command(
        ["ruff", "check", "code/", "tests/"],
        "Initial Ruff check on code and tests"
    )

    # Run initial format check
    print("\n--- Running initial format check ---")
    success_format = run_command(
        ["black", "--check", "code/", "tests/"],
        "Initial Black check on code and tests"
    )

    if success and success_format:
        print("\n✓ All linting and formatting checks passed.")
        print("Configuration is ready. Run 'ruff check . --fix' and 'black .' to apply fixes.")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above and fix issues.")
        print("You can run 'ruff check . --fix' and 'black .' to automatically fix formatting issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())