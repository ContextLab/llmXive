"""
Script to run linting and formatting checks for the project.
"""
import subprocess
import sys
from pathlib import Path

def run_command(command: list[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {description} passed\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}\n")
        return False

def main():
    """Main entry point for linting and formatting checks."""
    print("=" * 60)
    print("Running Linting and Formatting Checks")
    print("=" * 60 + "\n")

    # Run Ruff check
    ruff_success = run_command(
        ["ruff", "check", "."],
        "Ruff lint check"
    )

    # Run Black format check
    black_success = run_command(
        ["black", "--check", "."],
        "Black format check"
    )

    if ruff_success and black_success:
        print("All checks passed!")
        sys.exit(0)
    else:
        print("Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
