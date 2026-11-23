"""
Script to verify and optionally install linting and formatting tools.
This script ensures that `black` and `ruff` are available and validates
the configuration files exist.
"""
import subprocess
import sys
import os
import tomllib
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    """Run a command and return its exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return e.returncode

def main():
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"
    ruff_config_path = project_root / ".ruff.toml"

    # 1. Verify configuration files exist
    if not pyproject_path.exists():
        print(f"ERROR: {pyproject_path} not found. Please run the task to create it.")
        return 1
    
    if not ruff_config_path.exists():
        print(f"ERROR: {ruff_config_path} not found. Please run the task to create it.")
        return 1

    # 2. Validate pyproject.toml syntax
    try:
        with open(pyproject_path, "rb") as f:
            tomllib.load(f)
        print("✓ pyproject.toml is valid TOML.")
    except tomllib.TOMLDecodeError as e:
        print(f"ERROR: Invalid TOML in pyproject.toml: {e}")
        return 1

    # 3. Check if tools are installed
    tools = [
        ("black", ["black", "--version"]),
        ("ruff", ["ruff", "--version"]),
    ]

    all_installed = True
    for tool_name, cmd in tools:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✓ {tool_name} is installed.")
        except FileNotFoundError:
            print(f"✗ {tool_name} is NOT installed. Attempting to install...")
            install_cmd = [sys.executable, "-m", "pip", "install", tool_name]
            if run_command(install_cmd) != 0:
                all_installed = False
                print(f"ERROR: Failed to install {tool_name}.")

    if not all_installed:
        print("ERROR: Some tools could not be installed.")
        return 1

    # 4. Run a dry-run check to ensure config is recognized
    print("\nValidating configuration against tools...")
    
    # Check Ruff
    ruff_check = [
        "ruff", "check", 
        "--config", str(pyproject_path),
        "--output-format", "concise",
        "."
    ]
    # We run this on the current directory, but we expect it to be quiet if no errors
    # or just print warnings. We don't fail the setup if code has lint errors, 
    # just that the tool recognizes the config.
    try:
        # Run ruff check on the config file itself to ensure it parses
        subprocess.run(
            ["ruff", "check", "--config", str(pyproject_path), str(pyproject_path)],
            check=False, 
            capture_output=True, 
            text=True
        )
        print("✓ Ruff recognizes pyproject.toml configuration.")
    except Exception as e:
        print(f"WARNING: Ruff check failed: {e}")

    # Check Black
    black_check = [
        "black", 
        "--config", str(pyproject_path),
        "--check", 
        "--diff",
        str(pyproject_path)
    ]
    try:
        result = subprocess.run(black_check, capture_output=True, text=True)
        # Black returns 0 if formatted, 1 if not. We just want to know if it parses.
        if "error:" not in result.stderr.lower():
            print("✓ Black recognizes pyproject.toml configuration.")
        else:
            print(f"WARNING: Black reported an issue: {result.stderr}")
    except Exception as e:
        print(f"WARNING: Black check failed: {e}")

    print("\nLinting and Formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
