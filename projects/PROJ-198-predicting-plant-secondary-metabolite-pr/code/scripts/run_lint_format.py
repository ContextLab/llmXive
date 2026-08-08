"""
Script to run linting (ruff) and formatting (black) checks.
Usage: python code/scripts/run_lint_format.py [--fix]
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> None:
    """Run a shell command and raise on failure."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    if result.returncode != 0 and check:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run linting and formatting checks.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply fixes for linting issues and format code.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    code_dir = project_root / "code"

    if args.fix:
        # Run ruff with --fix
        try:
            run_command(["ruff", "check", "--fix", str(code_dir)])
        except subprocess.CalledProcessError:
            # Ruff might exit non-zero if fixes were applied but some remain
            pass

        # Run black
        run_command(["black", str(code_dir)])

        # Run ruff again to ensure no issues remain after black formatting
        run_command(["ruff", "check", str(code_dir)])
    else:
        # Check mode (default)
        # Run ruff check
        run_command(["ruff", "check", str(code_dir)])

        # Run black --check
        run_command(["black", "--check", str(code_dir)])

    print("Linting and formatting checks passed.")

if __name__ == "__main__":
    main()