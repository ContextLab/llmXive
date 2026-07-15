"""
Script to verify linting and formatting tool installation and basic configuration.
This script ensures that ruff, black, and flake8 are installed and can be invoked.
"""
import subprocess
import sys
import shutil

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report success/failure."""
    print(f"Checking: {description}...")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        print(f"  ✓ {description} is available.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {description} failed: {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print(f"  ✗ {description} not found. Ensure it is installed.")
        return False

def main():
    print("Verifying Linting and Formatting Tool Installation...")
    print("-" * 50)

    tools = [
        (["ruff", "--version"], "Ruff"),
        (["black", "--version"], "Black"),
        (["flake8", "--version"], "Flake8"),
    ]

    all_ok = True
    for cmd, desc in tools:
        if not run_command(cmd, desc):
            all_ok = False

    print("-" * 50)
    if all_ok:
        print("All tools are installed and configured.")
        print("To run linting: ruff check code/")
        print("To run formatting: black code/")
        print("To run flake8: flake8 code/")
        return 0
    else:
        print("Some tools are missing or misconfigured.")
        print("Please install them via: pip install ruff black flake8")
        return 1

if __name__ == "__main__":
    sys.exit(main())
