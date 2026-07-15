import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return its exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return 1

def main() -> int:
    """Run black and ruff checks to verify formatting/linting rules."""
    print("=== Verifying Code Formatting and Linting ===\n")
    
    # Run Black check
    black_exit_code = run_command(["black", "--check", "."])
    if black_exit_code == 0:
        print("✓ Black formatting check passed.\n")
    else:
        print("✗ Black formatting check failed. Run 'black .' to fix.\n")
    
    # Run Ruff check
    ruff_exit_code = run_command(["ruff", "check", "."])
    if ruff_exit_code == 0:
        print("✓ Ruff linting check passed.\n")
    else:
        print("✗ Ruff linting check failed. Run 'ruff check --fix' to attempt fixes.\n")
    
    # Determine overall success
    if black_exit_code == 0 and ruff_exit_code == 0:
        print("All formatting and linting checks passed.")
        return 0
    else:
        print("Some checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())