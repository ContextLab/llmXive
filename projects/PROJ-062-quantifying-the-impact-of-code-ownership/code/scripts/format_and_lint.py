"""
Script to run formatting (black/isort) and linting (flake8) checks.
This script is intended to be run from the code/ directory.

Usage:
    python scripts/format_and_lint.py --check   # Run checks only (CI mode)
    python scripts/format_and_lint.py           # Run formatting fixes
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd: list[str], check: bool = False) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Format and lint code")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run checks only without modifying files (CI mode)"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print(f"Working in: {project_root}")

    if args.check:
        # Check mode: verify formatting and linting
        print("\n--- Running isort (check mode) ---")
        if not run_command(["isort", "--check-only", "."], check=True):
            print("ERROR: isort check failed. Run without --check to fix.")
            return 1

        print("\n--- Running black (check mode) ---")
        if not run_command(["black", "--check", "."], check=True):
            print("ERROR: black check failed. Run without --check to fix.")
            return 1

        print("\n--- Running flake8 ---")
        if not run_command(["flake8", "."], check=True):
            print("ERROR: flake8 found issues.")
            return 1

        print("\n✅ All checks passed!")
        return 0
    else:
        # Fix mode: apply formatting
        print("\n--- Running isort ---")
        run_command(["isort", "."])

        print("\n--- Running black ---")
        run_command(["black", "."])

        print("\n--- Running flake8 (report only) ---")
        run_command(["flake8", "."])

        print("\n✅ Formatting complete. Please review flake8 output above.")
        return 0

if __name__ == "__main__":
    sys.exit(main())