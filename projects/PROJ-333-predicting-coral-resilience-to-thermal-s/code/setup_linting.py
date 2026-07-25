"""
Utility module to install and verify linting and formatting tools.
This script ensures flake8, pylint, black, and isort are installed and configured.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run a shell command and raise an error if it fails."""
    print(f"Running: {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"  -> {description} completed successfully.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"  -> Error running {description}: {e.stderr}")
        raise RuntimeError(f"Failed to {description}: {e.stderr}")

def install_tools():
    """Install linting and formatting tools."""
    tools = [
        "flake8",
        "pylint",
        "black",
        "isort",
    ]
    for tool in tools:
        run_command(f"{sys.executable} -m pip install {tool}", f"Installing {tool}")

def verify_tools():
    """Verify that all tools are accessible and show versions."""
    tools = {
        "flake8": "flake8 --version",
        "pylint": "pylint --version",
        "black": "black --version",
        "isort": "isort --version",
    }
    for name, cmd in tools.items():
        try:
            run_command(cmd, f"Verifying {name}")
        except RuntimeError as e:
            print(f"Warning: Could not verify {name}: {e}")

def main():
    """Main entry point for the setup script."""
    print("Setting up linting and formatting environment...")
    install_tools()
    verify_tools()
    print("Linting and formatting tools configured successfully.")

if __name__ == "__main__":
    main()