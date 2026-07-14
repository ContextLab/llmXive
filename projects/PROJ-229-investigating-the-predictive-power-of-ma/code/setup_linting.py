import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list) -> bool:
    """
    Run a shell command and return True if successful.
    """
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """
    Initialize linting and formatting tools configuration.
    This script ensures the configuration files (pyproject.toml) exist
    and prompts the user to install the dev dependencies if not already done.
    """
    print("Configuring linting and formatting tools...")
    
    # Check if pyproject.toml exists (it should from T002/T005 artifacts)
    if not Path("pyproject.toml").exists():
        print("Error: pyproject.toml not found. Please run project initialization first.")
        sys.exit(1)

    # Verify dev dependencies are installed
    tools = ["black", "flake8", "isort"]
    missing = []
    
    for tool in tools:
        try:
            subprocess.run([sys.executable, "-m", tool, "--version"], 
                         capture_output=True, check=True)
            print(f"✓ {tool} is installed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
            print(f"✗ {tool} is NOT installed.")

    if missing:
        print(f"\nMissing tools: {', '.join(missing)}")
        print("Please install them via: pip install -e '.[dev]'")
        print("Or manually: pip install black flake8 isort pytest pytest-cov")
        sys.exit(1)
    
    print("\nAll linting tools are configured and ready.")
    print("To run linters manually:")
    print("  black --check code/ tests/")
    print("  flake8 code/ tests/")
    print("  isort --check-only code/ tests/")

if __name__ == "__main__":
    main()
