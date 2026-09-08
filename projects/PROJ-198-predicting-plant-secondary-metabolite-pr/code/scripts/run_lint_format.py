"""
Script to run linting (ruff) and formatting (black) checks.
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> bool:
    """Run a shell command. Returns True if successful."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        if check:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")
        return False
    return True

def main() -> None:
    parser = argparse.ArgumentParser(description="Run linting and formatting checks.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply automatic fixes (ruff --fix, black).",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent

    # Run Ruff
    ruff_cmd = ["ruff", "check", str(project_root)]
    if args.fix:
        ruff_cmd.append("--fix")
    try:
        run_command(ruff_cmd)
        print("✓ Ruff check passed.")
    except RuntimeError:
        print("✗ Ruff check failed.")
        sys.exit(1)

    # Run Black
    black_cmd = ["black", "--check", str(project_root)]
    if args.fix:
        black_cmd = ["black", str(project_root)]
        try:
            run_command(black_cmd)
            print("✓ Black formatting applied.")
        except RuntimeError:
            print("✗ Black formatting failed.")
            sys.exit(1)
    else:
        try:
            run_command(black_cmd)
            print("✓ Black formatting check passed.")
        except RuntimeError:
            print("✗ Black formatting check failed. Run with --fix to apply.")
            sys.exit(1)

    print("All checks passed.")

if __name__ == "__main__":
    main()
