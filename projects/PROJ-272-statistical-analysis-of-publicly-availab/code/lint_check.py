"""
Utility script to run linting and formatting checks.
This script is used to verify the project adheres to the configured style guidelines.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list, check: bool = True) -> int:
    """
    Run a command and return the exit code.

    Args:
        cmd: List of command arguments.
        check: If True, raise an exception if the command fails.

    Returns:
        The exit code of the command.
    """
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        if check:
            raise
        return e.returncode

def main():
    """Run linting and formatting checks."""
    print("Running linting and formatting checks...")
    
    # Check if ruff is available
    try:
        run_command(["ruff", "--version"])
    except FileNotFoundError:
        print("Error: ruff not found. Please install it via 'pip install ruff' or 'pre-commit'.")
        sys.exit(1)

    # Check if black is available
    try:
        run_command(["black", "--version"])
    except FileNotFoundError:
        print("Error: black not found. Please install it via 'pip install black' or 'pre-commit'.")
        sys.exit(1)

    # Run ruff check
    print("\n--- Running Ruff ---")
    try:
        run_command(["ruff", "check", "."], check=False)
    except Exception as e:
        print(f"Ruff check failed: {e}")

    # Run black check (diff mode)
    print("\n--- Running Black ---")
    try:
        run_command(["black", "--check", "."], check=False)
    except Exception as e:
        print(f"Black check failed: {e}")

    print("\nLinting and formatting checks complete.")

if __name__ == "__main__":
    main()