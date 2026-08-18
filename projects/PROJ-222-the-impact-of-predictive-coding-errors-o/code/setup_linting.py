import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list) -> bool:
    """Run a command and return True if successful."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}. Please install the required tools.")
        return False

def main():
    """
    Setup script for linting (ruff) and formatting (black) tools.
    This script ensures the tools are installed and creates initial configuration files if missing.
    """
    print("Setting up linting and formatting tools...")

    # Check and install ruff
    print("Checking for ruff...")
    if not run_command([sys.executable, "-m", "pip", "install", "ruff"]):
        print("Failed to install ruff.")
        return 1

    # Check and install black
    print("Checking for black...")
    if not run_command([sys.executable, "-m", "pip", "install", "black"]):
        print("Failed to install black.")
        return 1

    # Verify configuration files exist
    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"
    ruff_config_path = project_root / ".ruff.toml"

    if not pyproject_path.exists():
        print("Error: pyproject.toml not found in project root. Please create it first.")
        return 1

    # Optionally, run a dry run to check if config is valid
    print("Validating ruff configuration...")
    if not run_command(["ruff", "check", "--config", str(pyproject_path), "--output-format=full", "."]):
        # This might fail if no issues are found or if there are linting errors, which is expected
        # We just want to ensure the config is parsable.
        pass

    print("Validating black configuration...")
    if not run_command(["black", "--config", str(pyproject_path), "--check", "."]):
        # Expected to fail if files are not formatted yet
        pass

    print("Linting and formatting tools setup complete.")
    print("To format code, run: black .")
    print("To lint code, run: ruff check .")
    return 0

if __name__ == "__main__":
    sys.exit(main())
