"""
Linting and formatting runner for the project.
Executes ruff (linter) and black (formatter) on the code/ directory.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main() -> int:
    """Execute linting and formatting checks."""
    # Determine the project root (assumed to be where this script is called from or parent)
    # Since the task is to configure tools in code/, we run them against code/
    target_dir = "code"

    if not os.path.isdir(target_dir):
        print(f"Error: Directory '{target_dir}' not found.")
        return 1

    # 1. Check formatting with black (in check mode)
    # We use black via the module runner to ensure it uses the installed version
    black_check_cmd = [sys.executable, "-m", "black", "--check", "--diff", target_dir]
    exit_code = run_command(black_check_cmd)
    if exit_code != 0:
        print("\n--- Formatting failed. Please run 'python code/run_lint.py format' to fix. ---\n")

    # 2. Check linting with ruff
    ruff_check_cmd = [sys.executable, "-m", "ruff", "check", target_dir]
    exit_code = run_command(ruff_check_cmd)
    if exit_code != 0:
        print("\n--- Linting failed. Please fix the errors above. ---\n")

    return exit_code

def format_code() -> int:
    """Format the code using black and ruff."""
    target_dir = "code"
    
    # Format with black
    black_cmd = [sys.executable, "-m", "black", target_dir]
    run_command(black_cmd)

    # Format with ruff (fixes auto-fixable issues)
    ruff_cmd = [sys.executable, "-m", "ruff", "check", "--fix", target_dir]
    return run_command(ruff_cmd)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "format":
        sys.exit(format_code())
    else:
        sys.exit(main())
