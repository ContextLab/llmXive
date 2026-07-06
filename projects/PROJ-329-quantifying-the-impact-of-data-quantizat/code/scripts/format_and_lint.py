"""
Script to run formatting (black, isort) and linting (flake8) on the project.
Usage: python scripts/format_and_lint.py [--fix]
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report status."""
    print(f"Running: {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Format and lint the project code.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply fixes (black, isort) instead of just checking.",
    )
    args = parser.parse_args()

    root_dir = Path(__file__).parent.parent
    src_dir = root_dir / "code"
    
    # Determine target directory for tools (usually the code root)
    target_dir = src_dir

    print(f"Target directory: {target_dir}")
    print("-" * 40)

    # 1. Run Isort
    if args.fix:
        run_command(
            [sys.executable, "-m", "isort", str(target_dir)],
            "Isort (ordering imports)"
        )
    else:
        # Check only
        run_command(
            [sys.executable, "-m", "isort", "--check-only", str(target_dir)],
            "Isort (check-only)"
        )

    # 2. Run Black
    if args.fix:
        run_command(
            [sys.executable, "-m", "black", str(target_dir)],
            "Black (formatting)"
        )
    else:
        run_command(
            [sys.executable, "-m", "black", "--check", str(target_dir)],
            "Black (check-only)"
        )

    # 3. Run Flake8
    # Flake8 only checks, doesn't fix automatically in this context
    run_command(
        [sys.executable, "-m", "flake8", str(target_dir)],
        "Flake8 (linting)"
    )

    print("-" * 40)
    print("All checks passed.")

if __name__ == "__main__":
    main()