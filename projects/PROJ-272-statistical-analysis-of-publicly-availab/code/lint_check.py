"""
Utility script to run linting and formatting checks manually.
Usage: python code/lint_check.py
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, check=True, capture_output=False, text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error in {description}: {e}")
        return False

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    print(f"Checking project at: {project_root}")
    print("-" * 50)

    # Run Ruff (Linter)
    if not run_command(
        [sys.executable, "-m", "ruff", "check", str(code_dir), str(tests_dir)],
        "Ruff Linting"
    ):
        print("Ruff check failed. Please fix the errors above.")
        return 1

    # Run Ruff (Formatter/Black equivalent)
    # Note: ruff format is the new black replacement in ruff
    if not run_command(
        [sys.executable, "-m", "ruff", "format", "--check", str(code_dir), str(tests_dir)],
        "Ruff Formatting (Black)"
    ):
        print("Ruff format check failed. Run 'ruff format' to fix.")
        return 1

    print("-" * 50)
    print("All linting and formatting checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())