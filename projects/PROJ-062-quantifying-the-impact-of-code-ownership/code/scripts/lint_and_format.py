"""
Script to run linting (flake8) and formatting (black) checks on the codebase.
This script ensures code quality standards are met before committing or running tests.
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(command: list[str], check: bool = True) -> None:
    """Run a shell command and raise an error if it fails."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}")
        if e.stderr:
            print(e.stderr)
        if check:
            sys.exit(e.returncode)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run linting and formatting checks.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix formatting issues with black."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail immediately on any linting error."
    )
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent

    print(f"Linting and formatting for project root: {root_dir}")
    print("-" * 50)

    # Step 1: Run Black (Formatting)
    # If --fix is provided, black will fix issues automatically
    # If not, it will check and report issues
    black_cmd = ["black", "--check", "--diff"]
    if args.fix:
        print("Fixing formatting with Black...")
        black_cmd = ["black"]
    else:
        print("Checking formatting with Black (no auto-fix)...")

    run_command(black_cmd + [str(root_dir)], check=False)

    # Step 2: Run Flake8 (Linting)
    print("-" * 50)
    print("Running Flake8...")
    flake8_cmd = ["flake8", str(root_dir)]
    
    # If strict mode, we fail on any error
    # If not strict, we just report but don't exit with error code unless configured
    run_command(flake8_cmd, check=args.strict)

    print("-" * 50)
    print("Linting and formatting check complete.")

if __name__ == "__main__":
    main()
