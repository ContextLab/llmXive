"""
Script to verify and initialize linting/formatting configurations.
This script ensures that ruff and black are installed and configurations
are valid. It does not modify project files directly but validates the setup.
"""
import subprocess
import sys
import tomllib
from pathlib import Path

def check_command_available(cmd: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def validate_config_files() -> bool:
    """Validate that configuration files exist and are readable."""
    root = Path(__file__).resolve().parent.parent.parent
    ruff_config = root / ".ruff.toml"
    black_config = root / ".black.toml"

    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found.")
        return False
    
    if not black_config.exists():
        print(f"Error: {black_config} not found.")
        return False

    try:
        with open(ruff_config, "rb") as f:
            tomllib.load(f)
        print("✓ .ruff.toml is valid TOML")
    except Exception as e:
        print(f"Error parsing .ruff.toml: {e}")
        return False

    try:
        with open(black_config, "rb") as f:
            tomllib.load(f)
        print("✓ .black.toml is valid TOML")
    except Exception as e:
        print(f"Error parsing .black.toml: {e}")
        return False

    return True

def main():
    """Main entry point for the linting setup verification."""
    print("Checking linting and formatting tools...")
    
    # Check for ruff
    if not check_command_available("ruff"):
        print("Warning: 'ruff' not found. Install with: pip install ruff")
        return 1
    print("✓ ruff is installed")

    # Check for black
    if not check_command_available("black"):
        print("Warning: 'black' not found. Install with: pip install black")
        return 1
    print("✓ black is installed")

    # Validate configs
    if not validate_config_files():
        print("Error: Configuration validation failed.")
        return 1

    print("\nLinting and formatting setup is valid.")
    return 0

if __name__ == "__main__":
    sys.exit(main())