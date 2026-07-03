"""
Utility script to verify linting and formatting tool installation.
This script checks if flake8, black, and isort are installed and
can be invoked via the system path.
"""
import subprocess
import sys
import os

def check_command(cmd: str, args: list) -> bool:
    """Check if a command exists and returns a valid version/help."""
    try:
        result = subprocess.run(
            [cmd] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False

def main():
    tools = [
        ("flake8", ["--version"]),
        ("black", ["--version"]),
        ("isort", ["--version"]),
        ("mypy", ["--version"]),
    ]

    print("Checking linting and formatting tools...")
    all_good = True

    for tool, args in tools:
        if check_command(tool, args):
            print(f"✓ {tool} is installed and accessible.")
        else:
            print(f"✗ {tool} is missing or not in PATH. Run: pip install {tool}")
            all_good = False

    if not all_good:
        print("\nPlease install missing tools using the requirements.txt provided.")
        sys.exit(1)

    # Verify configuration files exist
    config_files = [".flake8", "pyproject.toml"]
    print("\nChecking configuration files...")
    for cfg in config_files:
        if os.path.exists(cfg):
            print(f"✓ {cfg} found.")
        else:
            print(f"⚠ {cfg} not found in project root.")

    print("\nLinting setup verification complete.")

if __name__ == "__main__":
    main()