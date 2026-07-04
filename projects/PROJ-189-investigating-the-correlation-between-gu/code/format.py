"""
Utility script to run Black formatting and Ruff linting.
Usage: python code/format.py [--check] [--fix]
"""
import subprocess
import sys
import argparse

def run_command(cmd_args, description):
    """Run a command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd_args)}")
    result = subprocess.run(cmd_args)
    if result.returncode != 0:
        print(f"❌ {description} failed.")
        return False
    print(f"✅ {description} passed.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run formatting and linting checks.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check formatting and linting without modifying files."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix linting errors where possible."
    )
    args = parser.parse_args()

    code_dir = "code"
    tests_dir = "tests"
    success = True

    # Black formatting
    black_args = [
        "black",
        "--config", f"{code_dir}/pyproject.toml" if False else None, # Fallback to default if no config
        code_dir,
        tests_dir,
    ]
    if args.check:
        black_args.append("--check")
    if not args.fix:
        black_args.append("--diff")
    
    # Remove None values
    black_args = [a for a in black_args if a is not None]

    if not run_command(black_args, "Black formatting"):
        success = False

    # Ruff linting
    ruff_args = [
        "ruff",
        "check",
        code_dir,
        tests_dir,
    ]
    if args.fix:
        ruff_args.append("--fix")
    if args.check:
        # In check mode, we just report errors
        pass

    if not run_command(ruff_args, "Ruff linting"):
        success = False

    if success:
        print("\n✅ All checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
