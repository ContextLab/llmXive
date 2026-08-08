"""
Script to verify and install linting and formatting tools (ruff, black).
This script is idempotent and ensures the environment is ready for development.
"""
import subprocess
import sys
import os
from pathlib import Path

def check_package_installed(package_name):
    """Check if a package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_packages(packages):
    """Install a list of packages using pip."""
    print(f"Installing packages: {packages}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("Packages installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install packages: {e}")
        sys.exit(1)

def verify_cpu_only():
    """
    Verify that we are running in a CPU-only environment if applicable.
    For linting tools, this is less critical but good practice to check env.
    """
    # Linting tools don't typically use GPU, but we verify the project context
    print("Verifying environment context...")
    # Placeholder for any specific CPU-only checks if needed for linting
    return True

def verify_imports():
    """Verify that ruff and black are importable or available via CLI."""
    print("Verifying tool availability...")
    
    tools = [
        ("ruff", ["ruff", "--version"]),
        ("black", ["black", "--version"])
    ]

    for name, cmd in tools:
        try:
            subprocess.check_call(cmd)
            print(f"  ✓ {name} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  ✗ {name} is NOT available. Please install it.")
            return False
    
    return True

def main():
    """Main entry point for the setup script."""
    print("Starting linting and formatting setup...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required.")
        sys.exit(1)

    # Define required packages
    dev_packages = ["ruff>=0.1.0", "black>=23.0.0"]

    # Install if missing
    missing = []
    for pkg in dev_packages:
        pkg_name = pkg.split(">=")[0].split("<")[0]
        if not check_package_installed(pkg_name):
            missing.append(pkg)

    if missing:
        install_packages(missing)
    else:
        print("All required packages are already installed.")

    # Verify environment
    verify_cpu_only()

    # Verify tools are callable
    if not verify_imports():
        print("Verification failed. Please check your PATH and installation.")
        sys.exit(1)

    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()
