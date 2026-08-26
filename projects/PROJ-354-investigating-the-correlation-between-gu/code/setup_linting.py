"""
Setup script to configure linting and formatting tools (ruff, black).
This script validates the environment and ensures configuration files are present.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  ✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {description} failed with return code {e.returncode}")
        if e.stderr:
            print(f"  Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"  ✗ {description} failed: command not found")
        return False

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    print("=== Linting and Formatting Setup ===\n")
    
    # Check for Python version
    if sys.version_info < (3, 10):
        print("⚠ Warning: Python 3.10+ is recommended for this project.")
    
    # Install tools if not present
    tools_to_install = []
    if not check_tool_installed("black"):
        tools_to_install.append("black")
    if not check_tool_installed("ruff"):
        tools_to_install.append("ruff")
    
    if tools_to_install:
        print("Installing missing tools:")
        install_cmd = [sys.executable, "-m", "pip", "install"] + tools_to_install
        if not run_command(install_cmd, "pip install " + " ".join(tools_to_install)):
            print("Failed to install required tools. Please install manually.")
            sys.exit(1)
        print()
    
    # Verify configuration files exist
    root = Path(__file__).resolve().parent.parent
    ruff_config = root / ".ruff.toml"
    pyproject_config = root / "pyproject.toml"
    
    if not ruff_config.exists():
        print(f"⚠ Warning: {ruff_config} not found. Please create it.")
    else:
        print(f"✓ Found {ruff_config}")
    
    if not pyproject_config.exists():
        print(f"⚠ Warning: {pyproject_config} not found. Please create it.")
    else:
        print(f"✓ Found {pyproject_config}")
    
    # Run linting check (dry run)
    print("\n--- Validating Ruff Configuration ---")
    if not run_command(["ruff", "check", "--output-format=concise", "."], "Ruff check (dry run)"):
        print("Note: Linting issues found. Run 'ruff check --fix' to auto-fix where possible.")
    
    # Run formatting check (dry run)
    print("\n--- Validating Black Configuration ---")
    if not run_command(["black", "--check", "."], "Black check (dry run)"):
        print("Note: Formatting issues found. Run 'black .' to auto-format.")
    
    print("\n=== Setup Complete ===")
    print("To run linter:   ruff check .")
    print("To auto-fix:     ruff check --fix .")
    print("To format code:  black .")
    print("To check format: black --check .")

if __name__ == "__main__":
    main()