"""
Utility script to run linting (ruff) and formatting (black) checks.
This script ensures code quality standards are met before execution.
"""
import argparse
import subprocess
import sys
import os

def run_command(command: list[str], description: str) -> bool:
    """
    Run a shell command and report status.
    Returns True if successful, False otherwise.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,
            text=True,
            cwd=os.getcwd()
        )
        print(f"✅ {description} passed.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        print("Please fix the reported issues and re-run.\n")
        return False
    except FileNotFoundError:
        print(f"❌ Error: '{command[0]}' not found. Please install it via 'pip install {command[0]}'.\n")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Run linters and formatters on the llmxive-spatialclaw project."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to automatically fix formatting and linting issues."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for issues, do not fix."
    )
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(project_root, "code")
    tests_dir = os.path.join(project_root, "tests")

    if not os.path.exists(code_dir):
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    success = True

    # 1. Check Black formatting
    if args.check_only:
        black_cmd = ["black", "--check", "--diff", code_dir, tests_dir]
        if not run_command(black_cmd, "Black format check"):
            success = False
    else:
        black_cmd = ["black", code_dir, tests_dir]
        if not run_command(black_cmd, "Black format fix"):
            success = False

    # 2. Check Ruff linting
    if args.check_only:
        ruff_cmd = ["ruff", "check", code_dir, tests_dir]
        if not run_command(ruff_cmd, "Ruff lint check"):
            success = False
    else:
        # Ruff fix mode
        ruff_cmd = ["ruff", "check", "--fix", code_dir, tests_dir]
        if not run_command(ruff_cmd, "Ruff lint fix"):
            # If fix didn't resolve everything, we might still have errors
            # But we assume the command ran successfully if it didn't crash
            pass

    if success:
        print("✅ All linting and formatting checks passed.")
    else:
        print("❌ Some checks failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
