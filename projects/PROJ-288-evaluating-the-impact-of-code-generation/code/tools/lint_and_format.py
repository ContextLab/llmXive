"""
Script to run linting and formatting on the codebase.
Uses ruff for linting and black for formatting.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main() -> None:
    """Run linting and formatting checks."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    # Check if code directories exist
    if not code_dir.exists():
        print(f"Error: {code_dir} does not exist.")
        sys.exit(1)

    # Run ruff check
    print("\n--- Running Ruff Linter ---")
    ruff_exit = run_command([sys.executable, "-m", "ruff", "check", str(code_dir), str(tests_dir)])

    # Run black check (dry run)
    print("\n--- Running Black Formatter Check ---")
    black_exit = run_command([sys.executable, "-m", "black", "--check", str(code_dir), str(tests_dir)])

    if ruff_exit == 0 and black_exit == 0:
        print("\n✅ All checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed.")
        if ruff_exit != 0:
            print("   Fix linting errors with: ruff check . --fix")
        if black_exit != 0:
            print("   Fix formatting with: black .")
        sys.exit(1)


if __name__ == "__main__":
    main()