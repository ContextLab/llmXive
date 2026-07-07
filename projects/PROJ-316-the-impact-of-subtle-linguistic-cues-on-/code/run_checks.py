"""
Script to run linting (flake8) and formatting (black) checks.
This script validates the codebase against the configured standards.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main() -> int:
    """Run all linting and formatting checks."""
    code_dir = Path(__file__).parent
    os.chdir(code_dir)

    exit_code = 0

    # Run flake8
    print("\n--- Running Flake8 ---")
    exit_code |= run_command(["flake8", "."])

    # Run black check
    print("\n--- Running Black (check only) ---")
    exit_code |= run_command(["black", "--check", "."])

    if exit_code == 0:
        print("\n✅ All checks passed!")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")

    return exit_code

if __name__ == "__main__":
    sys.exit(main())