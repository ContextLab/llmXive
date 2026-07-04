"""
Utility script to run linting (flake8) and formatting (black) checks.
This script is used to verify code quality before submission.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str):
    """Run a shell command and print the result."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✓ {description} passed.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed.")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        print(f"Error code: {e.returncode}\n")
        return False

def main():
    """Main entry point for linting and formatting."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    print("=" * 60)
    print("Running Code Quality Checks")
    print("=" * 60 + "\n")

    # 1. Check Black Formatting
    # We run black in check mode (diff only) to ensure code is formatted
    black_check_passed = run_command(
        ["python", "-m", "black", "--check", "--diff", str(code_dir)],
        "Black Format Check"
    )

    # 2. Check Flake8 Linting
    # We run flake8 on the code directory
    flake8_check_passed = run_command(
        ["python", "-m", "flake8", str(code_dir)],
        "Flake8 Lint Check"
    )

    if black_check_passed and flake8_check_passed:
        print("All code quality checks passed!")
        sys.exit(0)
    else:
        print("Some code quality checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
