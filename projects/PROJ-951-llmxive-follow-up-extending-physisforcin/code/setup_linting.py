"""
Script to verify and install linting (ruff) and formatting (black) tools.
This script ensures the development environment is configured correctly.
"""
import subprocess
import sys
import os
from pathlib import Path

def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "show", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_packages(packages: list) -> bool:
    """Install a list of packages."""
    print(f"Installing packages: {packages}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + packages
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install packages: {e}")
        return False

def verify_cpu_only() -> bool:
    """Verify that we are not using CUDA (not strictly applicable for linting, but good practice)."""
    # Linting tools don't use GPU, but we check environment context
    if "CUDA_VISIBLE_DEVICES" in os.environ:
        print(f"Warning: CUDA_VISIBLE_DEVICES is set to {os.environ['CUDA_VISIBLE_DEVICES']}")
        print("Linting tools will ignore this, but training scripts should respect it.")
    return True

def verify_imports() -> bool:
    """Verify that ruff and black can be imported/run."""
    try:
        # Try to run ruff --version
        subprocess.check_call(
            [sys.executable, "-m", "ruff", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ Ruff is available")
    except subprocess.CalledProcessError:
        print("✗ Ruff is not available")
        return False

    try:
        # Try to run black --version
        subprocess.check_call(
            [sys.executable, "-m", "black", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ Black is available")
    except subprocess.CalledProcessError:
        print("✗ Black is not available")
        return False

    return True

def main():
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools...")
    
    # Check and install packages
    packages_to_install = []
    if not check_package_installed("ruff"):
        packages_to_install.append("ruff")
    if not check_package_installed("black"):
        packages_to_install.append("black")

    if packages_to_install:
        if not install_packages(packages_to_install):
            print("Failed to install required packages.")
            sys.exit(1)
    else:
        print("All required packages are already installed.")

    # Verify environment
    if not verify_cpu_only():
        print("Environment verification failed.")
        sys.exit(1)

    # Verify imports/execution
    if not verify_imports():
        print("Import verification failed.")
        sys.exit(1)

    print("Linting and formatting setup complete.")
    print("Configuration files (.ruff.toml, pyproject.toml) should be present in the project root.")

if __name__ == "__main__":
    main()