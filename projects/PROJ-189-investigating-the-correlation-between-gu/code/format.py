"""
Formatting and linting utility script.
Provides commands to run black and ruff against the project codebase.
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with code {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run formatting and linting tools.")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check formatting/linting without fixing."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix issues where possible."
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    # Determine black arguments
    black_args = [sys.executable, "-m", "black"]
    if args.check_only:
        black_args.append("--check")
    if args.fix:
        black_args.append("--diff") # or just run without --check to fix in place
    
    black_targets = [str(code_dir), str(tests_dir)]

    # Determine ruff arguments
    ruff_args = [sys.executable, "-m", "ruff", "check"]
    if args.fix:
        ruff_args.append("--fix")
    if args.check_only and not args.fix:
        ruff_args.append("--exit-zero") # ruff check exits 0 if no errors, but we want to see output
    
    ruff_targets = [str(code_dir), str(tests_dir)]

    success = True

    # Run Black
    success &= run_command(
        black_args + black_targets,
        "Black formatting check" if args.check_only else "Black formatting"
    )

    # Run Ruff
    success &= run_command(
        ruff_args + ruff_targets,
        "Ruff linting check" if args.check_only else "Ruff linting"
    )

    if not success:
        sys.exit(1)

    if args.check_only:
        print("\nAll checks passed.")
    else:
        print("\nFormatting and linting complete.")

if __name__ == "__main__":
    main()
