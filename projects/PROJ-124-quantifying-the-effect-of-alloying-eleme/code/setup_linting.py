import os
import sys
import subprocess
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and available in PATH."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=10
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def run_formatting_check() -> bool:
    """Run Black formatting check."""
    if not check_tool_installed("black"):
        print("Error: black is not installed. Run: pip install black")
        return False

    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print("Black formatting check passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Black formatting check failed:\n{e.stderr.decode()}")
        return False

def run_linting_check() -> bool:
    """Run Ruff linting check."""
    if not check_tool_installed("ruff"):
        print("Error: ruff is not installed. Run: pip install ruff")
        return False

    try:
        result = subprocess.run(
            ["ruff", "check", "code/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print("Ruff linting check passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ruff linting check failed:\n{e.stderr.decode()}")
        return False

def main():
    """Main entry point for linting setup verification."""
    print("=== Linting and Formatting Setup Verification ===")
    
    black_ok = run_formatting_check()
    ruff_ok = run_linting_check()
    
    if black_ok and ruff_ok:
        print("\nAll checks passed!")
        return 0
    else:
        print("\nSome checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())