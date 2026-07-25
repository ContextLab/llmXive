"""
Convenience script to run linting and formatting checks against the codebase.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> bool:
    """Run a command and return True if it succeeds."""
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def main() -> int:
    """Run linters and formatters."""
    print("Running code quality checks...")

    # Run Ruff
    print("\n1. Running Ruff...")
    if not run_command(["ruff", "check", "code/"]):
        print("   ⚠ Ruff found issues.")
    else:
        print("   ✓ Ruff passed.")

    # Run Black
    print("\n2. Running Black...")
    if not run_command(["black", "--check", "code/"]):
        print("   ⚠ Black found formatting issues.")
    else:
        print("   ✓ Black passed.")

    print("\nChecks complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())