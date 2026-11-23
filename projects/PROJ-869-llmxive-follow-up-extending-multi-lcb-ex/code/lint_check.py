"""
Utility script to run linting (ruff) and formatting checks (black) on the project.
This script verifies that the codebase adheres to the configured standards.
"""
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str]) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=False,
            text=True,
        )
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {command[0]}")
        print("Please ensure 'ruff' and 'black' are installed.")
        return 1


def main() -> None:
    """Run linting and formatting checks."""
    print("=" * 60)
    print("Running Linting and Formatting Checks")
    print("=" * 60)

    # Determine project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    exit_code = 0

    # 1. Check formatting with black
    print("\n[1/2] Checking formatting with Black...")
    # Use --check to verify without modifying files
    if run_command(["black", "--check", "code", "tests", "data"]):
        print("❌ Black check failed. Run 'black code tests data' to fix.")
        exit_code = 1
    else:
        print("✅ Black check passed.")

    # 2. Check linting with ruff
    print("\n[2/2] Checking linting with Ruff...")
    # Use 'check' command (default in newer versions, or explicitly 'ruff check')
    if run_command(["ruff", "check", "code", "tests"]):
        print("❌ Ruff check failed. Run 'ruff check --fix code tests' to fix.")
        exit_code = 1
    else:
        print("✅ Ruff check passed.")

    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ All checks passed!")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
    print("=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()