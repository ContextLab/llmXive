"""
Script to run linting (flake8) and formatting (black) checks on the codebase.
This script is designed to be run as: python code/run_lint_format.py
"""
import subprocess
import sys
from pathlib import Path

def run_command(command: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    # Check if tools are installed
    try:
        subprocess.run([sys.executable, "-m", "flake8", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("flake8 is not installed. Please install it via requirements.txt")
        sys.exit(1)

    try:
        subprocess.run([sys.executable, "-m", "black", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("black is not installed. Please install it via requirements.txt")
        sys.exit(1)

    # Run linting
    lint_success = run_command(
        [sys.executable, "-m", "flake8", str(code_dir)],
        "Linting with flake8"
    )

    # Run formatting check (dry run)
    format_success = run_command(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        "Formatting check with black"
    )

    if lint_success and format_success:
        print("\n✅ All checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
