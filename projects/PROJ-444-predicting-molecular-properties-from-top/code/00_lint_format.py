"""
Linting and Formatting Script.
Runs ruff check and black formatting on the project codebase.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return e.returncode

def main() -> None:
    """Entry point for linting and formatting."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    if not code_dir.exists() and not tests_dir.exists():
        print("Error: Neither 'code/' nor 'tests/' directory found in project root.")
        sys.exit(1)

    target_dirs = []
    if code_dir.exists():
        target_dirs.append(str(code_dir))
    if tests_dir.exists():
        target_dirs.append(str(tests_dir))

    # 1. Run Linter (Ruff)
    # --fix attempts to auto-fix issues, --exit-non-zero-on-fix ensures we fail if fixes were needed but not applied immediately
    lint_cmd = [
        sys.executable, "-m", "ruff", "check",
        "--fix",
        "--exit-non-zero-on-fix",
        *target_dirs
    ]
    lint_exit_code = run_command(lint_cmd)

    # 2. Run Formatter (Black)
    format_cmd = [
        sys.executable, "-m", "black",
        "--check", # Check only, do not modify files
        *target_dirs
    ]
    format_exit_code = run_command(format_cmd)

    if lint_exit_code != 0 or format_exit_code != 0:
        print("\nLinting or Formatting failed. Please fix issues and re-run.")
        sys.exit(1)

    print("\nLinting and Formatting checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()