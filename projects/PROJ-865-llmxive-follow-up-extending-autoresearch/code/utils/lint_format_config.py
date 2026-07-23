"""
Utility module to run linting and formatting checks on the project codebase.
Ensures consistency across the llmXive pipeline code.
"""
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

def run_linter(check: bool = True) -> Tuple[bool, str]:
    """
    Run Ruff linter on the code directory.

    Args:
        check: If True, only check (exit code 0 if clean). If False, fix issues.

    Returns:
        Tuple of (success: bool, message: str)
    """
    code_root = Path(__file__).parent.parent
    command = [
        sys.executable, "-m", "ruff",
        "check" if check else "check --fix",
        str(code_root)
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=code_root
        )
        if result.returncode == 0:
            return True, "Linting passed successfully."
        else:
            return False, f"Linting failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Ruff not found. Please install it: pip install ruff"
    except Exception as e:
        return False, f"Error running linter: {str(e)}"

def run_formatter(check: bool = True) -> Tuple[bool, str]:
    """
    Run Black formatter on the code directory.

    Args:
        check: If True, only check (exit code 0 if clean). If False, format files.

    Returns:
        Tuple of (success: bool, message: str)
    """
    code_root = Path(__file__).parent.parent
    command = [
        sys.executable, "-m", "black",
        "--check" if check else "",
        str(code_root)
    ]
    # Remove empty string if check is False
    command = [c for c in command if c]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=code_root
        )
        if result.returncode == 0:
            return True, "Formatting check passed successfully."
        else:
            return False, f"Formatting check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Black not found. Please install it: pip install black"
    except Exception as e:
        return False, f"Error running formatter: {str(e)}"

def main():
    """Main entry point for linting and formatting."""
    import argparse

    parser = argparse.ArgumentParser(description="Run linting and formatting checks")
    parser.add_argument("--fix", action="store_true", help="Fix issues instead of just checking")
    args = parser.parse_args()

    lint_success, lint_msg = run_linter(check=not args.fix)
    format_success, format_msg = run_formatter(check=not args.fix)

    print(lint_msg)
    print(format_msg)

    if not (lint_success and format_success):
        sys.exit(1)

    print("All checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()