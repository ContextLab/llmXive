"""
Linting utility for running ruff checks on the project codebase.
"""
import subprocess
import sys
import os

def run_command(command: list) -> int:
    """Run a linting command and return the exit code."""
    try:
        result = subprocess.run(command, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'ruff' not found. Please install it via 'pip install ruff'.")
        return 1

def main():
    """Main entry point for running linters."""
    print("Running linters...")
    
    # Run ruff check
    exit_code = run_command([sys.executable, "-m", "ruff", "check", "code/"])
    
    if exit_code == 0:
        print("Linting passed!")
    else:
        print("Linting failed. Please fix the issues above.")
        print("Tip: Run 'ruff check --fix code/' to automatically fix some issues.")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
