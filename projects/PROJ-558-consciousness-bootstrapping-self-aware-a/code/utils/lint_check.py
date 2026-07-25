"""
Lint and Format Check Script for llmXive Project.

This script runs `ruff check` and `black --check` on the `code/` directory.
It exits with a non-zero status if any linting or formatting errors are found,
ensuring CI fails appropriately.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a command and return its exit code."""
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"ERROR: Command not found: {cmd[0]}")
        print("Please ensure 'ruff' and 'black' are installed in your environment.")
        return 1

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(project_root, "code")

    if not os.path.isdir(code_dir):
        print(f"ERROR: Directory not found: {code_dir}")
        sys.exit(1)

    print(f"Checking lint and format in: {code_dir}")
    print("=" * 50)

    exit_code = 0

    # 1. Run Ruff Check
    print("\n[1/2] Running Ruff Check...")
    ruff_cmd = ["ruff", "check", code_dir]
    ruff_code = run_command(ruff_cmd)
    if ruff_code != 0:
        print("RUFF CHECK FAILED.")
        exit_code = 1
    else:
        print("RUFF CHECK PASSED.")

    # 2. Run Black Check
    print("\n[2/2] Running Black Check...")
    black_cmd = ["black", "--check", code_dir]
    black_code = run_command(black_cmd)
    if black_code != 0:
        print("BLACK CHECK FAILED.")
        exit_code = 1
    else:
        print("BLACK CHECK PASSED.")

    print("\n" + "=" * 50)
    if exit_code == 0:
        print("SUCCESS: All linting and formatting checks passed.")
    else:
        print("FAILURE: One or more checks failed. Please fix the issues above.")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()