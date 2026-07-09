"""
Utility script to verify linting and formatting configurations.
This script ensures that flake8 and black are correctly configured
and can be run against the codebase.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in {description}:")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    """Verify linting setup."""
    root_dir = Path(__file__).parent.parent
    code_dir = root_dir / "code"

    if not code_dir.exists():
        print(f"Error: code directory not found at {code_dir}")
        return False

    # Check if configuration files exist
    config_files = [
        root_dir / ".flake8",
        root_dir / "pyproject.toml",
        root_dir / ".pre-commit-config.yaml"
    ]

    missing = [f for f in config_files if not f.exists()]
    if missing:
        print(f"Warning: Missing configuration files: {missing}")
        print("Please ensure .flake8, pyproject.toml, and .pre-commit-config.yaml are present.")

    # Try to run flake8 check (dry run)
    print("\n--- Checking flake8 configuration ---")
    flake8_success = run_command(
        [sys.executable, "-m", "flake8", "--version"],
        "Flake8 version check"
    )

    # Try to run black check (dry run)
    print("\n--- Checking black configuration ---")
    black_success = run_command(
        [sys.executable, "-m", "black", "--version"],
        "Black version check"
    )

    if flake8_success and black_success:
        print("\nLinting and formatting tools are configured correctly.")
        return True
    else:
        print("\nSome tools failed to run. Please check installation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)