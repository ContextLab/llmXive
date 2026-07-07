"""
Linting and Formatting Runner for llmXive Project.

This script verifies that the codebase adheres to the configured
linting (ruff) and formatting (black) standards.

Usage:
    python code/00_lint_format.py
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        return result.returncode
    except FileNotFoundError:
        print(f"ERROR: Command not found: {cmd[0]}")
        print("Please ensure 'ruff' and 'black' are installed.")
        return 1

def main() -> int:
    """Execute linting and formatting checks."""
    print("--- Starting Lint and Format Validation ---\n")

    # Check for ruff
    print("[1/2] Running Ruff Linter...")
    ruff_code = run_command([sys.executable, "-m", "ruff", "check", "."])
    if ruff_code != 0:
        print("❌ Ruff check failed. Please fix the errors above.\n")
        return 1
    print("✅ Ruff check passed.\n")

    # Check for black
    print("[2/2] Running Black Formatter...")
    black_code = run_command([sys.executable, "-m", "black", "--check", "."])
    if black_code != 0:
        print("❌ Black check failed. Please run 'black .' to fix formatting.\n")
        return 1
    print("✅ Black check passed.\n")

    print("--- All checks passed successfully! ---")
    return 0

if __name__ == "__main__":
    sys.exit(main())
