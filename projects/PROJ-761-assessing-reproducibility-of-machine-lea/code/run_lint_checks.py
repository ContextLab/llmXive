"""
Script to run initial linting (ruff) and formatting (black) checks.
This task verifies the configuration validity on the project structure.
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    print(f"--- {description} ---")
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Passed")
            return True
        else:
            print("✗ Failed")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
    except FileNotFoundError:
        print(f"✗ Command not found: {cmd[0]}")
        print("Ensure 'ruff' and 'black' are installed in the environment.")
        return False

def main():
    print("Running initial linting and formatting configuration checks...")
    print(f"Current directory: {os.getcwd()}")
    print("-" * 40)

    # Check ruff configuration
    ruff_success = run_command(
        ["ruff", "check", "."],
        "Ruff Linting Check"
    )

    # Check black configuration (format check only, no writing)
    black_success = run_command(
        ["black", "--check", "."],
        "Black Formatting Check"
    )

    print("-" * 40)
    if ruff_success and black_success:
        print("All checks passed. Configuration is valid.")
        sys.exit(0)
    else:
        print("Some checks failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
