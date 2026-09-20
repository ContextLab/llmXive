"""
Linting and Formatting Tool Runner.

This module provides functions to run Ruff (linting) and Black (formatting)
against the project codebase. It checks for tool availability and executes
the necessary commands.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from config import ensure_dirs


def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a command and return True if successful.
    
    Args:
        cmd: Command and arguments as a list.
        description: Human-readable description of the action.
        
    Returns:
        True if the command succeeded, False otherwise.
    """
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Please install {' '.join(cmd[:2])}.")
        return False


def check_dependencies() -> bool:
    """
    Check if required tools (ruff, black) are installed.
    
    Returns:
        True if all dependencies are found, False otherwise.
    """
    tools = [
        ("ruff", "ruff --version"),
        ("black", "black --version"),
    ]
    all_found = True
    for name, cmd in tools:
        try:
            subprocess.run(cmd.split(), check=True, capture_output=True)
            print(f"✓ {name} is installed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"✗ {name} is NOT installed. Install with: pip install {name}")
            all_found = False
    return all_found


def run_lint() -> bool:
    """
    Run Ruff linter against the code directory.
    
    Returns:
        True if linting passes, False if errors are found or tool fails.
    """
    # Use ruff check with the project config
    cmd = ["ruff", "check", "code/"]
    return run_command(cmd, "Linting code with Ruff")


def run_format() -> bool:
    """
    Run Black formatter against the code directory.
    
    Returns:
        True if formatting completes, False if tool fails.
    """
    cmd = ["black", "code/"]
    return run_command(cmd, "Formatting code with Black")


def main() -> int:
    """
    Main entry point for linting and formatting tools.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    parser = argparse.ArgumentParser(
        description="Run linting and formatting tools for the project."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check code without modifying it (Black --check).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix linting issues (Ruff --fix).",
    )
    args = parser.parse_args()

    # Ensure directories exist (safety check)
    ensure_dirs()

    print("Checking dependencies...")
    if not check_dependencies():
        print("Aborting: Missing dependencies.")
        return 1

    if args.fix:
        print("Attempting to fix linting issues...")
        cmd = ["ruff", "check", "--fix", "code/"]
        if not run_command(cmd, "Fixing linting issues"):
            return 1

    print("\n--- Running Linter ---")
    lint_success = run_lint()
    
    if not lint_success:
        print("\nLinting failed. Please fix the issues above.")
        # If not --check-only, we might want to run formatter anyway, 
        # but typically lint failures block CI.
        # For this script, we return failure if linting fails.
        return 1

    print("\n--- Running Formatter ---")
    if args.check_only:
        cmd = ["black", "--check", "code/"]
        format_success = run_command(cmd, "Checking code format")
    else:
        format_success = run_format()

    if not format_success:
        print("\nFormatting check failed. Please run without --check-only to auto-fix.")
        return 1

    print("\n✓ All linting and formatting checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
