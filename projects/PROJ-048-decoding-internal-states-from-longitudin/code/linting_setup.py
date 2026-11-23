"""
Linting setup and utility functions for running flake8 and black checks.
This module provides helpers to execute linting commands and validate code quality.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

def run_command(command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command and return the return code, stdout, and stderr.

    Args:
        command: List of command arguments.
        cwd: Working directory for the command.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return (
            -1,
            "",
            f"Error: Command not found. Ensure {' '.join(command)} is installed.",
        )
    except Exception as e:
        return -1, "", f"Error executing command: {str(e)}"

def check_flake8() -> Tuple[bool, str]:
    """
    Run flake8 linting on the codebase.

    Returns:
        Tuple of (success, message)
    """
    flake8_path = Path(__file__).parent / ".flake8"
    if not flake8_path.exists():
        return False, "Configuration file .flake8 not found in code/"

    command = [
        sys.executable,
        "-m",
        "flake8",
        "--config=code/.flake8",
        "code/",
    ]

    returncode, stdout, stderr = run_command(command)

    if returncode == 0:
        return True, "All flake8 checks passed!"
    else:
        return False, f"flake8 found issues:\n{stdout}\n{stderr}"

def check_black() -> Tuple[bool, str]:
    """
    Run black formatting check on the codebase.

    Returns:
        Tuple of (success, message)
    """
    command = [sys.executable, "-m", "black", "--check", "--config=pyproject.toml", "code/"]

    returncode, stdout, stderr = run_command(command)

    if returncode == 0:
        return True, "All black formatting checks passed!"
    else:
        return False, f"black formatting issues found:\n{stdout}\n{stderr}"

def check_isort() -> Tuple[bool, str]:
    """
    Run isort import sorting check on the codebase.

    Returns:
        Tuple of (success, message)
    """
    command = [sys.executable, "-m", "isort", "--check-only", "--settings-path=pyproject.toml", "code/"]

    returncode, stdout, stderr = run_command(command)

    if returncode == 0:
        return True, "All isort import order checks passed!"
    else:
        return False, f"isort import order issues found:\n{stdout}\n{stderr}"

def run_all_checks() -> bool:
    """
    Run all linting and formatting checks.

    Returns:
        True if all checks pass, False otherwise.
    """
    checks = [
        ("flake8", check_flake8),
        ("black", check_black),
        ("isort", check_isort),
    ]

    all_passed = True

    for name, check_func in checks:
        print(f"\nRunning {name}...")
        success, message = check_func()
        print(message)

        if not success:
            all_passed = False

    return all_passed

def main():
    """Entry point for running linting checks."""
    print("=" * 60)
    print("Running Linting and Formatting Checks")
    print("=" * 60)

    success = run_all_checks()

    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: All checks passed!")
        sys.exit(0)
    else:
        print("FAILURE: Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()