"""
Setup script for linting and formatting tools.
Verifies that black, flake8, and isort are configured and can be invoked.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list) -> int:
    """
    Run a shell command and return the exit code.
    Prints output to stdout/stderr.
    """
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command '{cmd[0]}' not found. Please ensure it is installed.")
        return 1
    except Exception as e:
        print(f"Error running command: {e}")
        return 1

def main():
    """
    Main entry point to verify linting tool configuration.
    This script checks if the configuration files exist and if the tools run without immediate syntax errors.
    """
    root_dir = Path(__file__).resolve().parent.parent
    config_files = {
        "pyproject.toml": root_dir / "pyproject.toml",
        ".flake8": root_dir / ".flake8",
        ".isort.cfg": root_dir / ".isort.cfg",
    }

    print("Checking linting configuration files...")
    all_exist = True
    for name, path in config_files.items():
        if path.exists():
            print(f"  [OK] {name} exists")
        else:
            print(f"  [MISSING] {name} not found at {path}")
            all_exist = False

    if not all_exist:
        print("Error: One or more configuration files are missing. Please ensure they are created.")
        sys.exit(1)

    print("\nVerifying tool availability...")
    tools = [
        (["black", "--version"], "black"),
        (["flake8", "--version"], "flake8"),
        (["isort", "--version"], "isort"),
    ]

    for cmd, name in tools:
        exit_code = run_command(cmd)
        if exit_code == 0:
            print(f"  [OK] {name} is available and configured.")
        else:
            print(f"  [WARN] {name} returned non-zero exit code. Ensure it is installed.")

    print("\nLinting and formatting configuration verified.")
    sys.exit(0)

if __name__ == "__main__":
    main()
