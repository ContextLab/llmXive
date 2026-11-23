"""
Script to initialize and install pre-commit hooks for the project.
Executes 'pre-commit init' and 'pre-commit install' commands.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """
    Run a shell command and return True if successful.

    Args:
        command: List of command arguments.
        description: Human-readable description of the action.

    Returns:
        True if command succeeded, False otherwise.
    """
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        print(f"Success: {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {description}")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return code: {e.returncode}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Ensure 'pre-commit' is installed.")
        print("Install with: pip install pre-commit")
        return False


def main() -> int:
    """
    Main entry point for pre-commit setup.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Initializing pre-commit configuration...")

    # Step 1: Initialize pre-commit
    success_init = run_command(
        ["pre-commit", "init"],
        "Initialize pre-commit hooks"
    )

    if not success_init:
        print("Failed to initialize pre-commit. Aborting.")
        return 1

    # Step 2: Install pre-commit hooks
    success_install = run_command(
        ["pre-commit", "install"],
        "Install pre-commit hooks to .git/hooks"
    )

    if not success_install:
        print("Failed to install pre-commit hooks. Aborting.")
        return 1

    print("\nPre-commit setup completed successfully!")
    print("Hooks will now run automatically before each commit.")
    print("To run manually: pre-commit run --all-files")
    return 0


if __name__ == "__main__":
    sys.exit(main())