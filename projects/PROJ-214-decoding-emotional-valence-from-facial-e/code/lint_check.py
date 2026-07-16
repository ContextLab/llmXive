"""
Utility script to run linting and formatting checks.
Used to verify the configuration established in T003.
"""
import subprocess
import sys
import os

def run_command(command: list[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}...")
    try:
        result = subprocess.run(
            command, check=True, capture_output=False, text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Please install dependencies: {' '.join(command)}")
        return False

def main() -> int:
    """Run all configured linting and formatting checks."""
    print("=" * 50)
    print("Running Linting and Formatting Checks")
    print("=" * 50)

    checks = [
        (
            ["black", "--check", "."],
            "Black Formatting Check",
        ),
        (
            ["ruff", "check", "."],
            "Ruff Linting Check",
        ),
    ]

    all_passed = True
    for command, desc in checks:
        if not run_command(command, desc):
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("All checks passed.")
        return 0
    else:
        print("Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())