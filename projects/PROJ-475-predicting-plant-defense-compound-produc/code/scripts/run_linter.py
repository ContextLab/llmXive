"""
Script to validate linting and formatting configuration.
This script ensures that ruff and black are installed and configured correctly.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return the exit code."""
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        print("Please ensure 'ruff' and 'black' are installed.")
        print("Run: pip install -r requirements-dev.txt")
        return 1

def main() -> int:
    """Main entry point for the linting validation script."""
    print("Validating linting and formatting setup for llmXive project...")
    
    # Check if ruff is available
    ruff_version_code = run_command(["ruff", "--version"])
    if ruff_version_code != 0:
        return 1
    
    # Check if black is available
    black_version_code = run_command(["black", "--version"])
    if black_version_code != 0:
        return 1

    # Run ruff check
    print("\nRunning ruff check...")
    ruff_check_code = run_command(["ruff", "check", "."])
    
    # Run black check
    print("\nRunning black check...")
    black_check_code = run_command(["black", "--check", "."])

    if ruff_check_code == 0 and black_check_code == 0:
        print("\n✅ All linting and formatting checks passed!")
        return 0
    else:
        print("\n❌ Some checks failed. Run 'ruff check --fix .' and 'black .' to fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())