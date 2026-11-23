import os
import subprocess
import sys
from pathlib import Path

def check_config_files() -> bool:
    """Verify that linting and formatting config files exist."""
    project_root = Path(__file__).parent.parent
    ruff_config = project_root / "pyproject.toml"
    black_config = project_root / "pyproject.toml"
    pre_commit_config = project_root / ".pre-commit-config.yaml"

    if not ruff_config.exists():
        print("ERROR: pyproject.toml (for ruff/black config) not found.")
        return False
    if not pre_commit_config.exists():
        print("ERROR: .pre-commit-config.yaml not found.")
        return False

    print("Configuration files found.")
    return True

def install_dev_dependencies() -> bool:
    """Install development dependencies (ruff, black, pytest, etc.)."""
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-e", ".[dev]"
        ], cwd=Path(__file__).parent.parent)
        print("Development dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dev dependencies: {e}")
        return False

def initialize_pre_commit() -> bool:
    """Initialize pre-commit hooks."""
    try:
        subprocess.check_call(["pre-commit", "install"], cwd=Path(__file__).parent.parent)
        print("Pre-commit hooks installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install pre-commit hooks: {e}")
        return False

def run_linter() -> bool:
    """Run ruff linter."""
    try:
        subprocess.check_call(["ruff", "check", "."], cwd=Path(__file__).parent.parent)
        print("Linter passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Linter failed: {e}")
        return False

def run_formatter() -> bool:
    """Run black formatter."""
    try:
        subprocess.check_call(["black", "."], cwd=Path(__file__).parent.parent)
        print("Formatter completed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Formatter failed: {e}")
        return False

def main() -> int:
    """Main entry point for setup."""
    print("Setting up linting and formatting tools...")

    if not check_config_files():
        return 1

    if not install_dev_dependencies():
        return 1

    if not initialize_pre_commit():
        return 1

    print("Setup complete. Run 'ruff check .' and 'black .' to verify.")
    return 0

if __name__ == "__main__":
    sys.exit(main())