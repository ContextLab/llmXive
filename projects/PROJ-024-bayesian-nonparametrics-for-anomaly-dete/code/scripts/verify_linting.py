"""
Verification script for linting configuration.
Ensures all linting tools are properly configured and working.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_linting_check() -> Tuple[bool, str]:
    """Run linting checks and return status."""
    code_dir = Path(__file__).parent.parent

    # Run ruff check
    try:
        result = subprocess.run(
            ["ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        ruff_ok = result.returncode == 0
        ruff_output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "ruff check timed out"
    except FileNotFoundError:
        return False, "ruff not installed"

    # Run black check
    try:
        result = subprocess.run(
            ["black", "--check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        black_ok = result.returncode == 0
        black_output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "black check timed out"
    except FileNotFoundError:
        return False, "black not installed"

    if ruff_ok and black_ok:
        return True, "All linting checks passed"
    else:
        return False, f"ruff: {'✓' if ruff_ok else '✗'}, black: {'✓' if black_ok else '✗'}"

def main():
    """Verify linting setup."""
    print("Verifying linting configuration...")
    print("-" * 50)

    # Check tool availability
    tools = ["ruff", "black", "isort", "mypy"]
    for tool in tools:
        installed = check_tool_installed(tool)
        status = "✓" if installed else "✗"
        print(f"  {status} {tool}")

    print("-" * 50)

    # Run actual checks
    success, message = run_linting_check()
    status = "✓" if success else "✗"
    print(f"{status} {message}")

    if success:
        print("\nLinting setup verified successfully!")
        sys.exit(0)
    else:
        print("\nLinting verification failed. Please fix issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
