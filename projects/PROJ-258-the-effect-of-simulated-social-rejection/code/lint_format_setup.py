"""
Utility script to initialize and validate linting/formatting configuration.
This script ensures that flake8 and black are configured correctly 
and can be run against the codebase.
"""
import subprocess
import sys
import os
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and available."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "show", tool_name],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def run_linting() -> int:
    """Run flake8 linting."""
    print("Running flake8 linting...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "code/", "tests/"],
            cwd=os.getcwd(),
            capture_output=False,
        )
        return result.returncode
    except FileNotFoundError:
        print("ERROR: flake8 not found. Please install it: pip install flake8")
        return 1

def run_formatting_check() -> int:
    """Run black formatting check (diff mode)."""
    print("Running black formatting check...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--config", "pyproject.toml", "code/", "tests/"],
            cwd=os.getcwd(),
            capture_output=False,
        )
        return result.returncode
    except FileNotFoundError:
        print("ERROR: black not found. Please install it: pip install black")
        return 1

def main() -> int:
    """Main entry point."""
    print("=== Linting and Formatting Setup Verification ===\n")

    # Check dependencies
    tools = ["flake8", "black", "pytest"]
    missing = [t for t in tools if not check_tool_installed(t)]

    if missing:
        print(f"Missing tools: {', '.join(missing)}")
        print("Install them with: pip install flake8 black pytest")
        return 1

    # Run checks
    lint_code = run_linting()
    format_code = run_formatting_check()

    if lint_code == 0 and format_code == 0:
        print("\n✓ All checks passed!")
        return 0
    else:
        print("\n✗ Checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())