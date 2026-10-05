"""
Script to verify and initialize linting and formatting configuration for the project.
This script checks for the existence of pyproject.toml with ruff/black configs
and provides a command to run the linters.
"""
import os
import sys
import subprocess
from pathlib import Path

def check_config():
    """Check if pyproject.toml exists and contains ruff/black sections."""
    root = Path(__file__).parent
    pyproject_path = root / "pyproject.toml"

    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found in code/.")
        return False

    content = pyproject_path.read_text()
    has_black = "[tool.black]" in content
    has_ruff = "[tool.ruff]" in content

    if not has_black:
        print("WARNING: [tool.black] section not found in pyproject.toml")
    if not has_ruff:
        print("WARNING: [tool.ruff] section not found in pyproject.toml")

    if has_black and has_ruff:
        print("SUCCESS: Linting and formatting configuration found in pyproject.toml.")
        return True
    else:
        return False

def run_checks():
    """Run ruff and black checks (dry run) if installed."""
    root = Path(__file__).parent
    try:
        # Check ruff
        result_ruff = subprocess.run(
            ["ruff", "check", "."],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result_ruff.returncode == 0:
            print("Ruff check passed.")
        else:
            print("Ruff check found issues:")
            print(result_ruff.stdout)
            print(result_ruff.stderr)

        # Check black
        result_black = subprocess.run(
            ["black", "--check", "."],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result_black.returncode == 0:
            print("Black check passed.")
        else:
            print("Black check found issues (run 'black .' to fix).")
            # Don't print full diff to keep output clean, just summary
            if "would reformat" in result_black.stdout:
                print("Some files need reformatting.")
            else:
                print(result_black.stdout)

    except FileNotFoundError:
        print("INFO: ruff or black not installed in environment. Run 'pip install ruff black' to enable checks.")
    except subprocess.TimeoutExpired:
        print("ERROR: Linting checks timed out.")

def main():
    """Main entry point."""
    print("Checking linting configuration...")
    config_ok = check_config()
    
    if not config_ok:
        print("Configuration incomplete. Please ensure pyproject.toml has [tool.black] and [tool.ruff].")
        sys.exit(1)

    print("\nRunning linting checks (if tools are available)...")
    run_checks()
    print("\nLinting setup verification complete.")

if __name__ == "__main__":
    main()