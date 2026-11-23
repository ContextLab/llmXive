import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and print status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {description} failed with exit code {e.returncode}")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    """
    Entry point for linting and formatting.
    Usage:
      python code/make_lint_format.py check   -> Run ruff check (lint)
      python code/make_lint_format.py fix     -> Run ruff check --fix
      python code/make_lint_format.py format  -> Run black
      python code/make_lint_format.py all     -> Run check, fix, and format
    """
    if len(sys.argv) < 2:
        print("Usage: python code/make_lint_format.py [check|fix|format|all]")
        sys.exit(1)

    command = sys.argv[1].lower()
    project_root = Path(__file__).parent

    success = True

    if command in ("check", "all"):
        if not run_command(
            [sys.executable, "-m", "ruff", "check", str(project_root)],
            "Linting (ruff check)"
        ):
            success = False

    if command in ("fix", "all"):
        if not run_command(
            [sys.executable, "-m", "ruff", "check", "--fix", str(project_root)],
            "Auto-fixing (ruff check --fix)"
        ):
            # Note: ruff might fail if some issues are not auto-fixable
            print("Note: Some linting issues may require manual fixes.")
            # Do not set success = False here as --fix is best-effort

    if command in ("format", "all"):
        if not run_command(
            [sys.executable, "-m", "black", str(project_root)],
            "Formatting (black)"
        ):
            success = False

    if command == "check":
        # Explicitly check exit code for strict CI usage
        if not success:
            sys.exit(1)
    elif command == "all":
        # If check failed, exit 1, even if format succeeded
        if not success:
            sys.exit(1)

    print("\nAll requested operations completed.")

if __name__ == "__main__":
    main()