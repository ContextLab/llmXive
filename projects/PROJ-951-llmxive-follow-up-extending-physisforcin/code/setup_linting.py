import subprocess
import sys
import os
from pathlib import Path

def check_package_installed(package_name):
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_packages(packages):
    print(f"Installing packages: {', '.join(packages)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("Packages installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def verify_cpu_only():
    # Linting tools are CPU-only by nature, no specific verification needed
    print("Linting tools are CPU-safe.")
    return True

def verify_imports():
    missing = []
    if not check_package_installed("ruff"):
        missing.append("ruff")
    if not check_package_installed("black"):
        missing.append("black")
    
    if missing:
        print(f"Missing linting tools: {', '.join(missing)}")
        return False
    
    print("All linting tools verified.")
    return True

def main():
    """Main entry point for linting setup."""
    print("Setting up linting and formatting tools...")
    
    # Check if tools are installed
    if not verify_imports():
        print("Installing missing tools...")
        install_packages(["ruff", "black"])
    
    # Verify again after installation
    if not verify_imports():
        print("Failed to verify linting tools after installation.")
        sys.exit(1)
    
    print("Linting setup complete.")

if __name__ == "__main__":
    main()
