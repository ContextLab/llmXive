"""
Setup script to ensure linting (ruff) and formatting (black) tools are configured
and ready to run. This script verifies the presence of configuration files
and provides a helper to run the tools.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_config_files():
    """Check if required configuration files exist."""
    project_root = Path(__file__).parent.parent
    config_files = [
        "pyproject.toml",
        ".pre-commit-config.yaml",
    ]
    
    missing = []
    for cfg in config_files:
        if not (project_root / cfg).exists():
            missing.append(cfg)
    
    if missing:
        print(f"Error: Missing configuration files: {missing}")
        print("Please ensure T003 has been run to generate these files.")
        return False
    
    print("Configuration files found.")
    return True

def install_dev_dependencies():
    """Install dev dependencies including ruff, black, and pre-commit."""
    print("Checking/Installing dev dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            check=True,
            cwd=Path(__file__).parent.parent,
        )
        print("Dev dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dev dependencies: {e}")
        return False

def initialize_pre_commit():
    """Initialize pre-commit hooks."""
    print("Initializing pre-commit hooks...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pre_commit", "install"],
            check=True,
            cwd=Path(__file__).parent.parent,
        )
        print("Pre-commit hooks installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install pre-commit hooks: {e}")
        return False

def run_linter():
    """Run ruff linter on the project."""
    print("Running ruff linter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "src", "tests", "code"],
            cwd=Path(__file__).parent.parent,
        )
        if result.returncode == 0:
            print("Linter passed.")
        else:
            print("Linter found issues.")
        return result.returncode == 0
    except FileNotFoundError:
        print("Ruff not found. Please install it first.")
        return False

def run_formatter():
    """Run black formatter on the project."""
    print("Running black formatter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "src", "tests", "code"],
            cwd=Path(__file__).parent.parent,
        )
        if result.returncode == 0:
            print("Formatter check passed.")
        else:
            print("Files need formatting.")
        return result.returncode == 0
    except FileNotFoundError:
        print("Black not found. Please install it first.")
        return False

def main():
    """Main entry point for setup."""
    print("Setting up linting and formatting tools...")
    
    if not check_config_files():
        sys.exit(1)
    
    if not install_dev_dependencies():
        sys.exit(1)
    
    # Optional: initialize pre-commit
    # initialize_pre_commit()
    
    print("\nSetup complete. You can now run:")
    print("  python code/setup_linting_formatting.py run-lint")
    print("  python code/setup_linting_formatting.py run-format")
    print("  pre-commit run --all-files")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "run-lint":
            sys.exit(0 if run_linter() else 1)
        elif cmd == "run-format":
            sys.exit(0 if run_formatter() else 1)
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        main()