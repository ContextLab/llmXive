"""
Script to run Black and Ruff formatting/linting.
Usage: python scripts/format.py [--check]
"""
import argparse
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print(f"  ✓ {description} passed.")
            return True
        else:
            print(f"  ✗ {description} failed.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {description} failed with code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"  ✗ Command not found. Please ensure {' '.join(cmd[:2])} is installed.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Format and lint the project codebase.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check formatting/linting without modifying files.",
    )
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    src_dir = root_dir / "src"
    tests_dir = root_dir / "tests"

    if not src_dir.exists():
        print(f"Error: Source directory not found at {src_dir}")
        sys.exit(1)

    targets = [str(src_dir), str(tests_dir)]

    success = True

    # Run Black
    black_cmd = ["black"]
    if args.check:
        black_cmd.append("--check")
    black_cmd.extend(targets)
    if not run_command(black_cmd, "Black formatting"):
        success = False

    # Run Ruff
    ruff_cmd = ["ruff", "check"]
    if args.check:
        ruff_cmd.append("--fix") # Ruff can auto-fix some issues
        # Note: Ruff's --fix is often preferred over just check in dev loops,
        # but for strict "check" mode we might want to avoid auto-fix if not desired.
        # However, the task asks for configuration. Let's stick to standard check behavior.
        # Actually, ruff check --fix is the modern way to auto-fix.
        # If --check is passed to our script, we probably don't want auto-fixes.
        # Let's remove --fix if --check is active to be safe, or just use ruff check.
        ruff_cmd = ["ruff", "check"] 
        if not args.check:
             ruff_cmd.append("--fix")
    
    ruff_cmd.extend(targets)
    if not run_command(ruff_cmd, "Ruff linting"):
        success = False

    if success:
        print("\n✓ All checks passed.")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
