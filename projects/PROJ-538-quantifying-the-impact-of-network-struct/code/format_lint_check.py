"""
Utility script to run formatting and linting checks.
This script ensures the codebase adheres to the configured Black and Ruff standards.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        return 1

    print(f"Checking project at: {project_root}")

    # 1. Check formatting with Black
    if not run_command(
        [sys.executable, "-m", "black", "--check", "--diff", str(code_dir), str(tests_dir)],
        "Black formatting check"
    ):
        print("Fix formatting errors with: black code/ tests/")
        return 1

    # 2. Check linting with Ruff
    if not run_command(
        [sys.executable, "-m", "ruff", "check", str(code_dir), str(tests_dir)],
        "Ruff linting check"
    ):
        print("Fix linting errors with: ruff check --fix code/ tests/")
        return 1

    print("\n✅ All checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())