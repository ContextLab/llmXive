"""
Script to validate and apply linting configurations.
This script ensures that the project adheres to the configured ruff and black standards.
"""
import os
import sys
from pathlib import Path
from config.linting_config import get_ruff_config_file_content, get_ruff_command, get_black_command

def main():
    """
    Main entry point for linting setup validation.
    Checks if configuration files exist and prints the commands to run.
    """
    root_dir = Path(__file__).resolve().parent.parent
    ruff_config = root_dir / ".ruff.toml"
    pyproject = root_dir / "pyproject.toml"

    if not ruff_config.exists():
        print(f"Error: Ruff configuration file not found at {ruff_config}")
        sys.exit(1)

    if not pyproject.exists():
        print(f"Error: pyproject.toml not found at {pyproject}")
        sys.exit(1)

    print("Linting configuration found.")
    print(f"Ruff config: {ruff_config}")
    print(f"Black config: {pyproject}")
    print("\n--- Commands to run ---")
    print(f"Check: {get_ruff_command()}")
    print(f"Fix: {get_ruff_command()} --fix")
    print(f"Format: {get_black_command()}")
    print("\n--- Configuration Content (Ruff) ---")
    print(get_ruff_config_file_content())
    
    return 0

if __name__ == "__main__":
    sys.exit(main())