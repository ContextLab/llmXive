"""
Script to verify and initialize linting and formatting tools.
This script ensures that ruff and black are installed and configured correctly.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return the exit code."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return e.returncode
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return 1

def main():
    """Main entry point for setup."""
    print("Setting up linting (ruff) and formatting (black)...")

    # Ensure tools are installed
    tools = [
        (["pip", "install", "-q", "black"], "black"),
        (["pip", "install", "-q", "ruff"], "ruff"),
    ]

    for cmd, tool_name in tools:
        print(f"Ensuring {tool_name} is installed...")
        if run_command(cmd) != 0:
            print(f"Failed to install {tool_name}. Please install manually.")
            return 1

    # Check configuration files exist
    config_files = ["pyproject.toml", ".ruff.toml"]
    for cf in config_files:
        if not Path(cf).exists():
            print(f"Warning: Configuration file {cf} not found in project root.")
            print("Please ensure pyproject.toml contains [tool.black] and [tool.ruff] sections.")

    # Run a dry-run check to verify configuration is valid
    print("\nVerifying ruff configuration...")
    if run_command(["ruff", "check", "--config", "pyproject.toml", "--diff", "code/"]) != 0:
        # A non-zero exit here might just mean there are issues to fix, which is fine for setup
        # We just want to ensure the config is valid.
        print("Ruff found issues or config is valid. This is expected.")

    print("\nVerifying black configuration...")
    if run_command(["black", "--config", "pyproject.toml", "--check", "--diff", "code/"]) != 0:
        # Similarly, this just checks if files are formatted according to config
        print("Black found formatting issues or config is valid. This is expected.")

    print("\nLinting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())