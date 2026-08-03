"""
Script to run flake8 and black on the project codebase.
This script ensures code quality by checking for linting errors
and formatting issues according to the project's configuration.
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(command: list, description: str) -> bool:
    """
    Run a shell command and return True if successful.

    Args:
        command: List of command arguments
        description: Description of what the command does

    Returns:
        True if command succeeded, False otherwise
    """
    print(f"Running {description}...")
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✓ {description} passed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"✗ Command not found: {command[0]}")
        print("Please install the required tools (flake8, black) via:")
        print("  pip install -r requirements-dev.txt")
        return False

def main():
    """Main entry point for the linting and formatting script."""
    parser = argparse.ArgumentParser(
        description="Run linting and formatting checks on the project."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix formatting issues with black"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for issues, do not fix"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    all_passed = True

    # Run flake8
    flake8_cmd = [
        sys.executable, "-m", "flake8",
        str(code_dir),
        "--config=.flake8"
    ]
    if not run_command(flake8_cmd, "flake8 linting"):
        all_passed = False

    # Run black
    if args.fix:
        black_cmd = [
            sys.executable, "-m", "black",
            "--config=pyproject.toml",
            str(code_dir)
        ]
        if not run_command(black_cmd, "black formatting (fix mode)"):
            all_passed = False
    else:
        black_cmd = [
            sys.executable, "-m", "black",
            "--config=pyproject.toml",
            "--check",
            str(code_dir)
        ]
        if not run_command(black_cmd, "black formatting check"):
            all_passed = False

    # Summary
    print("\n" + "="*50)
    if all_passed:
        print("All checks passed!")
        sys.exit(0)
    else:
        print("Some checks failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()