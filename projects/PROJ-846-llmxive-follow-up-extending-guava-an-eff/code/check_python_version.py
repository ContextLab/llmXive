"""
Python version check script to verify Python 3.11+ is available.
This script ensures the runtime environment meets the minimum version requirement.
"""
import sys
import subprocess
import os
import json
from pathlib import Path

MIN_VERSION_MAJOR = 3
MIN_VERSION_MINOR = 11


def check_python_version() -> bool:
    """
    Check if the current Python interpreter is version 3.11 or higher.

    Returns:
        bool: True if version is sufficient, False otherwise.
    """
    current_version = sys.version_info
    is_sufficient = (
        current_version.major > MIN_VERSION_MAJOR or
        (current_version.major == MIN_VERSION_MAJOR and current_version.minor >= MIN_VERSION_MINOR)
    )

    if not is_sufficient:
        print(f"ERROR: Python {MIN_VERSION_MAJOR}.{MIN_VERSION_MINOR}+ is required.")
        print(f"Current version: {current_version.major}.{current_version.minor}.{current_version.micro}")
        return False

    print(f"Python version check passed: {current_version.major}.{current_version.minor}.{current_version.micro}")
    return True


def install_dependencies() -> None:
    """
    Install dependencies listed in requirements.txt if they exist.
    This is a helper function to ensure the environment is ready after version check.
    """
    requirements_path = Path(__file__).parent / "requirements.txt"
    if not requirements_path.exists():
        print("WARNING: requirements.txt not found at expected location.")
        return

    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)


def main() -> int:
    """
    Main entry point for the script.
    Returns 0 on success, 1 on failure.
    """
    if not check_python_version():
        return 1

    # Optional: Attempt to install dependencies if requested or if this is a setup flow
    # For now, we just verify the version as per task T002b.
    # If the project workflow requires auto-installation, uncomment the line below.
    # install_dependencies()

    return 0


if __name__ == "__main__":
    sys.exit(main())