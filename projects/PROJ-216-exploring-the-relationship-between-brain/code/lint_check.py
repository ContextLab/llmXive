"""
Linting and formatting verification script.
Checks code quality using ruff and black.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    """Run a command and return the exit code."""
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command '{' '.join(cmd)}' not found.")
        print("Please install dependencies: pip install ruff black")
        return 1

def main() -> int:
    """Run linting and formatting checks."""
    project_root = Path(__file__).parent
    print("Checking code style and formatting...")

    # Check ruff
    print("\n1. Running Ruff (linting)...")
    ruff_code = run_command(["ruff", "check", str(project_root)])
    if ruff_code == 0:
        print("   ✓ Ruff passed")
    else:
        print("   ✗ Ruff failed")

    # Check black
    print("\n2. Running Black (formatting check)...")
    black_code = run_command(["black", "--check", str(project_root)])
    if black_code == 0:
        print("   ✓ Black passed")
    else:
        print("   ✗ Black failed")

    if ruff_code == 0 and black_code == 0:
        print("\n✓ All checks passed!")
        return 0
    else:
        print("\n✗ Some checks failed. Run 'ruff check --fix' and 'black .' to fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
