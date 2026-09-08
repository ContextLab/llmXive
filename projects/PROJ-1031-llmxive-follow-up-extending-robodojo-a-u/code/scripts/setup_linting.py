"""
Script to set up linting and formatting tools.
"""
import subprocess
import sys
import os
import tomllib
from pathlib import Path

def run_command(cmd):
    """Run a command and print output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(result.stdout)
    return result.returncode == 0

def main():
    base = Path(__file__).parent.parent
    config_file = base / "pyproject.toml"
    
    if not config_file.exists():
        print(f"Error: {config_file} not found.")
        return False
    
    try:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        if "tool" not in config or "black" not in config["tool"]:
            print("Warning: Black config not found in pyproject.toml")
        if "tool" not in config or "ruff" not in config["tool"]:
            print("Warning: Ruff config not found in pyproject.toml")
    except Exception as e:
        print(f"Error reading config: {e}")
        return False
    
    # Install tools
    run_command([sys.executable, "-m", "pip", "install", "black", "ruff"])
    
    # Run linter
    run_command([sys.executable, "-m", "ruff", "check", str(base / "src")])
    
    # Run formatter (dry run)
    run_command([sys.executable, "-m", "black", "--check", str(base / "src")])
    
    print("Setup complete.")
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
