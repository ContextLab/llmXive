"""
Linting and Formatting Setup Script

This script configures the project for Ruff (linting) and Black (formatting)
by verifying the existence of configuration files and installing dependencies.
"""

import subprocess
import sys
import os
from pathlib import Path


def check_tool_installed(tool_name: str) -> bool:
    """Check if a specific tool is installed in the current environment."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "show", tool_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_tools():
    """Install required linting and formatting tools."""
    tools = ["black", "ruff", "pytest"]
    missing = [t for t in tools if not check_tool_installed(t)]

    if not missing:
        print("All linting and formatting tools are already installed.")
        return

    print(f"Installing missing tools: {', '.join(missing)}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + missing, check=True
        )
        print("Tools installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing tools: {e}", file=sys.stderr)
        sys.exit(1)


def verify_config_files():
    """Verify that configuration files exist in the project root."""
    project_root = Path(__file__).parent.parent
    config_files = ["pyproject.toml", ".ruff.toml", ".ruff_cache"]

    missing = []
    for f in config_files:
        if not (project_root / f).exists():
            missing.append(f)

    if missing:
        print(
            f"Warning: Configuration files missing in project root: {', '.join(missing)}"
        )
        print("Please ensure 'pyproject.toml' contains [tool.black] and [tool.ruff] sections.")
        return False
    else:
        print("Configuration files verified.")
        return True


def run_lint_check():
    """Run Ruff linter on the codebase."""
    print("Running Ruff linter...")
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            check=True,
            cwd=Path(__file__).parent.parent,
        )
        print("Linting passed.")
        return True
    except subprocess.CalledProcessError:
        print("Linting failed. Please fix the reported issues.")
        return False


def run_format_check():
    """Run Black formatter check on the codebase."""
    print("Running Black format check...")
    try:
        subprocess.run(
            [sys.executable, "-m", "black", "--check", "."],
            check=True,
            cwd=Path(__file__).parent.parent,
        )
        print("Formatting check passed.")
        return True
    except subprocess.CalledProcessError:
        print("Formatting check failed. Run 'black .' to fix.")
        return False


def main():
    """Main entry point for setup and verification."""
    print("--- Linting & Formatting Setup ---")

    # 1. Install tools if missing
    install_tools()

    # 2. Verify config files (pyproject.toml must exist with [tool.black] and [tool.ruff])
    if not verify_config_files():
        print("Setup incomplete due to missing configuration.")
        sys.exit(1)

    print("--- Setup Complete ---")
    print("To check linting: python -m ruff check .")
    print("To check formatting: python -m black --check .")
    print("To auto-fix formatting: black .")


if __name__ == "__main__":
    main()