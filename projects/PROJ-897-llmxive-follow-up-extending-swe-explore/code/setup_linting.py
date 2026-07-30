import os
import sys
from pathlib import Path
import subprocess

def ensure_requirements() -> None:
    """Ensure linting tools are installed."""
    tools = ["ruff", "black", "flake8"]
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Installing {tool}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])

def create_ruff_config() -> None:
    """Ruff configuration is handled in pyproject.toml."""
    print("Ruff configuration is embedded in code/pyproject.toml")

def create_black_config() -> None:
    """Black configuration is handled in pyproject.toml."""
    print("Black configuration is embedded in code/pyproject.toml")

def create_flake8_config() -> None:
    """Flake8 configuration is handled in pyproject.toml."""
    print("Flake8 configuration is embedded in code/pyproject.toml")

def main() -> None:
    """Entry point for the script."""
    print("Setting up linting and formatting...")
    ensure_requirements()
    create_ruff_config()
    create_black_config()
    create_flake8_config()
    print("Linting setup complete.")

if __name__ == "__main__":
    main()
