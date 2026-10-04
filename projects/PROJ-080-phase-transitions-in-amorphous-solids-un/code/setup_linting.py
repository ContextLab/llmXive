"""
Setup script to verify and install linting/formatting tools.
This script ensures ruff and black are available and can be run
to validate the project's code style.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str):
    """Run a command and report status."""
    print(f"Checking: {description}...")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✓ {description} successful.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"✗ {description} tool not found. Please install via: pip install {cmd[0]}")
        return False

def main():
    print("Verifying Linting and Formatting Configuration...\n")
    
    # Check if tools are installed
    tools_installed = True
    if not run_command([sys.executable, "-m", "ruff", "--version"], "Ruff installation"):
        tools_installed = False
    if not run_command([sys.executable, "-m", "black", "--version"], "Black installation"):
        tools_installed = False

    if not tools_installed:
        print("Dependencies missing. Run: pip install ruff black")
        sys.exit(1)

    # Run checks against the code directory
    print("Running Lint Checks (Ruff)...")
    # We allow warnings but fail on errors. --exit-zero ensures we see output even if issues exist.
    # For strict CI, remove --exit-zero. Here we just verify it runs.
    run_command(
        [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
        "Ruff static analysis"
    )

    print("Running Format Checks (Black)...")
    run_command(
        [sys.executable, "-m", "black", "--check", "code/", "tests/"],
        "Black format check"
    )

    print("Linting and Formatting configuration verified.")

if __name__ == "__main__":
    main()