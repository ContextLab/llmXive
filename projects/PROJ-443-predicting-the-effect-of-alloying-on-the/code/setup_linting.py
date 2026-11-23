"""
Script to configure linting and formatting tools for the project.
This sets up flake8, black, isort, and pre-commit hooks.
"""
import subprocess
import sys
import os
from pathlib import Path


def check_command(cmd: str) -> bool:
    """Check if a command is available in the system."""
    try:
        subprocess.run(
            [cmd, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_dev_dependencies() -> bool:
    """Install development dependencies for linting."""
    print("Installing development dependencies...")
    try:
        # Try installing from requirements-dev.txt if it exists
        req_file = Path("requirements-dev.txt")
        if req_file.exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"],
                check=True,
            )
            print("✓ Installed dependencies from requirements-dev.txt")
            return True

        # Fallback to individual packages
        packages = ["flake8", "black", "isort", "pre-commit", "pytest"]
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + packages,
            check=True,
        )
        print("✓ Installed linting dependencies")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def setup_pre_commit() -> bool:
    """Initialize pre-commit hooks."""
    print("Setting up pre-commit hooks...")
    try:
        # Install pre-commit hook
        subprocess.run(["pre-commit", "install"], check=True)
        print("✓ Pre-commit hooks installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install pre-commit hooks: {e}")
        return False


def verify_linting_tools() -> bool:
    """Verify that all linting tools are available."""
    tools = [
        ("flake8", "Flake8"),
        ("black", "Black"),
        ("isort", "isort"),
        ("pre-commit", "pre-commit"),
    ]

    all_good = True
    for cmd, name in tools:
        if check_command(cmd):
            print(f"✓ {name} is available")
        else:
            print(f"✗ {name} is NOT available")
            all_good = False

    return all_good


def main():
    """Main entry point for linting setup."""
    print("=" * 60)
    print("Setting up linting and formatting tools")
    print("=" * 60)

    # Check if tools are already available
    if verify_linting_tools():
        print("\n✓ All tools are already installed")
    else:
        print("\nInstalling missing tools...")
        if not install_dev_dependencies():
            print("\n✗ Failed to install dependencies. Exiting.")
            sys.exit(1)

        if not verify_linting_tools():
            print("\n✗ Some tools are still missing after installation.")
            sys.exit(1)

    # Setup pre-commit hooks
    if not setup_pre_commit():
        print("\n⚠ Pre-commit hooks could not be installed (may already exist).")

    print("\n" + "=" * 60)
    print("Linting setup complete!")
    print("=" * 60)
    print("\nYou can now run:")
    print("  - pre-commit run --all-files  (run all hooks on all files)")
    print("  - black .                     (format code)")
    print("  - flake8 .                    (lint code)")
    print("  - isort .                     (sort imports)")


if __name__ == "__main__":
    main()