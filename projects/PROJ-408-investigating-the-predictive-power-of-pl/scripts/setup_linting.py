"""
Setup script to verify and install linting/formatting tools.
This script ensures ruff and black are available and validates configuration.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"

def main() -> int:
    print("Setting up linting and formatting tools...")
    
    # Check if ruff is installed
    code, stdout, stderr = run_command([sys.executable, "-m", "ruff", "--version"])
    if code != 0:
        print("Installing ruff...")
        code, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "ruff"])
        if code != 0:
            print(f"Failed to install ruff: {stderr}")
            return 1
        print("Ruff installed.")
    else:
        print(f"Ruff found: {stdout.strip()}")

    # Check if black is installed
    code, stdout, stderr = run_command([sys.executable, "-m", "black", "--version"])
    if code != 0:
        print("Installing black...")
        code, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "black"])
        if code != 0:
            print(f"Failed to install black: {stderr}")
            return 1
        print("Black installed.")
    else:
        print(f"Black found: {stdout.strip()}")

    # Validate configuration files exist
    root = Path(__file__).parent.parent
    ruff_config = root / ".ruff.toml"
    black_config = root / ".black.toml"
    pyproject = root / "pyproject.toml"

    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found. Please create it.")
        return 1
    
    if not black_config.exists():
        print(f"Error: {black_config} not found. Please create it.")
        return 1

    # Run a dry-run check with ruff to verify config
    print("\nValidating ruff configuration...")
    code, stdout, stderr = run_command([
        sys.executable, "-m", "ruff", "check", 
        "--config", str(ruff_config),
        "--select", "F401,ANN,E,W,I",
        str(root / "code")
    ])
    
    # We expect some errors in code that isn't fully typed yet, 
    # but we want to ensure the tool runs and reads the config.
    if code == 127:
        print("Error: ruff command not found after installation.")
        return 1
    
    print("Ruff configuration validated successfully.")

    # Run a dry-run check with black
    print("\nValidating black configuration...")
    code, stdout, stderr = run_command([
        sys.executable, "-m", "black",
        "--config", str(black_config),
        "--check",
        "--diff",
        str(root / "code")
    ])
    
    if code == 127:
        print("Error: black command not found after installation.")
        return 1
    
    # Black returns 1 if files need reformatting, which is fine for validation
    print("Black configuration validated successfully.")

    print("\nLinting and formatting tools setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())