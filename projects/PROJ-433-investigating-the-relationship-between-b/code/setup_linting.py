"""
Setup script to configure and verify linting (ruff) and formatting (black) tools.
This script ensures configuration files exist and runs initial checks.
"""
import os
import sys
import subprocess
from pathlib import Path

def ensure_config_exists():
    """Ensure pyproject.toml exists with ruff/black configuration."""
    root = Path(__file__).parent.parent
    config_file = root / "pyproject.toml"

    if not config_file.exists():
        print("ERROR: pyproject.toml not found in project root.")
        print("Please run the setup task that creates the project structure and config.")
        return False

    # Basic validation: check if [tool.ruff] and [tool.black] sections exist
    content = config_file.read_text()
    if "[tool.ruff]" not in content:
        print("WARNING: [tool.ruff] section missing in pyproject.toml. Attempting to append defaults...")
        with open(config_file, "a") as f:
            f.write("\n[tool.ruff]\ntarget-version = 'py311'\nline-length = 88\nselect = ['E', 'W', 'F', 'I']\n")
        print("Added default ruff config. Please review pyproject.toml.")
    
    if "[tool.black]" not in content:
        print("WARNING: [tool.black] section missing in pyproject.toml. Attempting to append defaults...")
        with open(config_file, "a") as f:
            f.write("\n[tool.black]\nline-length = 88\ntarget-version = ['py311']\n")
        print("Added default black config. Please review pyproject.toml.")

    return True

def install_tools():
    """Install ruff and black if not present."""
    print("Checking/Installing linting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        print("Tools installed successfully.")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install linting tools. Please check pip environment.")
        return False

def run_format_check():
    """Run black --check to verify formatting."""
    print("Running Black format check...")
    try:
        # Check all .py files in the code directory
        result = subprocess.run(
            ["black", "--check", "--diff", "code/"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ All files are formatted correctly.")
            return True
        else:
            print("✗ Formatting issues found. Run 'black code/' to fix.")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("ERROR: 'black' command not found. Ensure it is installed.")
        return False

def run_lint_check():
    """Run ruff to verify linting rules."""
    print("Running Ruff lint check...")
    try:
        result = subprocess.run(
            ["ruff", "check", "code/"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ No linting issues found.")
            return True
        else:
            print("✗ Linting issues found.")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("ERROR: 'ruff' command not found. Ensure it is installed.")
        return False

def main():
    """Main entry point for setup_linting."""
    print("--- Setting up Linting and Formatting ---")
    
    if not ensure_config_exists():
        return 1

    if not install_tools():
        return 1

    # Optional: Run checks immediately to verify setup
    # Note: In a CI environment, these might be separate steps.
    # Here we run them to confirm the configuration works.
    format_ok = run_format_check()
    lint_ok = run_lint_check()

    if format_ok and lint_ok:
        print("\n✓ Linting and Formatting setup complete.")
        return 0
    else:
        print("\n⚠ Setup complete, but checks found issues. Please fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())