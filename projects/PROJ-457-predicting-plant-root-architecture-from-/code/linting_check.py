"""
Script to verify linting configuration is correct and code passes checks.
This script attempts to run black and flake8 checks.
It is designed to be run as: python code/linting_check.py
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"

def main() -> int:
    """Execute linting checks."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        return 1

    print("Running Black check...")
    black_code, black_out, black_err = run_command(["black", "--check", "--diff", str(code_dir)])
    if black_code == 0:
        print("✓ Black check passed.")
    else:
        print("✗ Black check failed.")
        if black_out:
            print(black_out)
        if black_err:
            print(black_err)

    print("\nRunning Flake8 check...")
    flake8_code, flake8_out, flake8_err = run_command(["flake8", str(code_dir)])
    if flake8_code == 0:
        print("✓ Flake8 check passed.")
    else:
        print("✗ Flake8 check failed.")
        if flake8_out:
            print(flake8_out)
        if flake8_err:
            print(flake8_err)

    # Return non-zero if any check failed
    if black_code != 0 or flake8_code != 0:
        print("\nLinting failed. Please fix the issues above.")
        return 1

    print("\nAll linting checks passed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())