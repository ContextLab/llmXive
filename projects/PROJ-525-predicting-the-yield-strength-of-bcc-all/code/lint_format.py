"""
Utility module for running linting and formatting tools.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """
    Run a subprocess command and return True if successful.
    
    Args:
        cmd: Command and arguments as a list.
        description: Human-readable description of the command.
        
    Returns:
        True if the command succeeded, False otherwise.
    """
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found in PATH: {cmd[0]}")
        print("Please install the required tool (e.g., 'pip install ruff black').")
        return False


def main() -> int:
    """
    Main entry point for linting and formatting checks.
    
    Returns:
        Exit code: 0 if all checks pass, 1 otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)
    
    print(f"Project root: {project_root}")
    print("-" * 60)
    
    # Run ruff check
    ruff_check_success = run_command(
        ["ruff", "check", "."],
        "Ruff Linting",
    )
    
    # Run black check
    black_check_success = run_command(
        ["black", "--check", "."],
        "Black Formatting Check",
    )
    
    print("-" * 60)
    if ruff_check_success and black_check_success:
        print("All linting and formatting checks passed!")
        return 0
    else:
        errors = []
        if not ruff_check_success:
            errors.append("Linting failed (ruff)")
        if not black_check_success:
            errors.append("Formatting check failed (black)")
        print(f"Failed: {', '.join(errors)}")
        print("To fix formatting, run: black .")
        print("To fix linting issues, run: ruff check --fix .")
        return 1


if __name__ == "__main__":
    sys.exit(main())