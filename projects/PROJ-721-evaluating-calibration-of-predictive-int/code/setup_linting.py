from __future__ import annotations
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Execute a shell command and raise on failure."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        raise

def main() -> None:
    """Verify that ruff and black are installed and configured."""
    # Verify installation
    run_command([sys.executable, "-m", "pip", "install", "ruff", "black"])
    
    # Verify configuration exists
    config_path = Path("pyproject.toml")
    if not config_path.exists():
        raise FileNotFoundError("pyproject.toml not found. Please run task T003 to create it.")
    
    # Run a dry check to ensure configuration is valid
    run_command([sys.executable, "-m", "ruff", "check", "--output-format=concise", "."])
    run_command([sys.executable, "-m", "black", "--check", "--diff", "."])
    
    print("Linting and formatting tools configured successfully.")

if __name__ == "__main__":
    main()