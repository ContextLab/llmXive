"""
Script to run linting (ruff) and formatting (black) checks on the project code.
Usage: python code/lint.py [--fix]
"""
import subprocess
import sys
import os

def run_command(command, description, check=True):
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=False,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode == 0:
            print(f"✓ {description} passed.\n")
        else:
            print(f"✗ {description} failed.\n")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}.\n")
        return False
    except FileNotFoundError:
        print(f"✗ Error: Command not found. Please ensure {command[0]} is installed.\n")
        print("Run: pip install -r code/requirements-dev.txt")
        return False

def main():
    """Main entry point for linting script."""
    args = sys.argv[1:]
    fix_mode = "--fix" in args

    print("=" * 50)
    print("LLMXive Linting & Formatting Runner")
    print("=" * 50 + "\n")

    # Determine target directory (code/)
    target_dir = "code"

    # 1. Run Ruff
    ruff_cmd = ["ruff", "check", target_dir]
    if fix_mode:
        ruff_cmd.append("--fix")
    ruff_passed = run_command(ruff_cmd, "Ruff Linting")

    # 2. Run Black
    black_cmd = ["black", "--check", target_dir]
    if fix_mode:
        # If fix mode is requested, we run black without --check to format
        black_cmd = ["black", target_dir]
        description = "Black Formatting"
    else:
        description = "Black Formatting Check"

    black_passed = run_command(black_cmd, description)

    if ruff_passed and black_passed:
        print("All checks passed! ✨")
        return 0
    else:
        if fix_mode:
            print("Some issues remain after fixing. Please review the output above.")
        else:
            print("Linting/Formatting failed. Run `python code/lint.py --fix` to attempt automatic fixes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
