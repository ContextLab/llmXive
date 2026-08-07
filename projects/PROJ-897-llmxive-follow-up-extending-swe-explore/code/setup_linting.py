"""
Setup script to ensure linting tools (ruff, black) are installed and configured.
This script is idempotent and can be run multiple times.
"""
import os
import sys
import subprocess
from pathlib import Path

def ensure_requirements():
    """Install ruff and black if not present."""
    print("Checking for ruff and black...")
    try:
        import ruff
        import black
        print("Linting tools already installed.")
    except ImportError:
        print("Installing linting tools...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        print("Linting tools installed successfully.")

def create_ruff_config():
    """Ensure ruff config exists in pyproject.toml (handled by file creation in T001b)."""
    # The config is now embedded in code/pyproject.toml
    # This function exists for legacy compatibility or if external config is needed later
    pass

def create_black_config():
    """Ensure black config exists in pyproject.toml (handled by file creation in T001b)."""
    pass

def create_flake8_config():
    """Ensure flake8 config exists if needed (currently using ruff)."""
    pass

def main():
    """Main entry point for setup_linting."""
    print("Starting linting setup...")
    ensure_requirements()
    create_ruff_config()
    create_black_config()
    create_flake8_config()
    print("Linting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())