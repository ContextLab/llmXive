"""
Setup script for linting (ruff) and formatting (black) tools.
This script ensures the necessary tools are installed and configured.
"""
import subprocess
import sys
import os
from pathlib import Path

def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_packages(packages: list):
    """Install required packages using pip."""
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    print(f"Installing: {' '.join(packages)}")
    subprocess.check_call(cmd)

def verify_cpu_only():
    """Verify that no GPU-specific configurations are forced (mostly for torch)."""
    # Linting tools don't have GPU dependencies, but we keep the pattern consistent
    pass

def verify_imports():
    """Verify that configured tools can be imported/run."""
    tools = [
        ("black", ["black", "--version"]),
        ("ruff", ["ruff", "--version"]),
    ]
    for name, cmd in tools:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ {name} is installed and working")
            else:
                print(f"⚠ {name} returned non-zero exit code: {result.stderr}")
        except FileNotFoundError:
            print(f"✗ {name} is not installed or not in PATH")

def main():
    """Main entry point for setup."""
    print("Setting up linting and formatting tools...")

    # Check and install dependencies
    needed = []
    if not check_package_installed("black"):
        needed.append("black")
    if not check_package_installed("ruff"):
        needed.append("ruff")

    if needed:
        install_packages(needed)
    else:
        print("All linting tools already installed.")

    verify_cpu_only()
    verify_imports()

    # Verify configuration files exist
    code_dir = Path(__file__).parent
    config_files = ["pyproject.toml", ".ruff.toml", ".pre-commit-config.yaml"]
    for f in config_files:
        if (code_dir / f).exists():
            print(f"✓ Configuration file {f} found")
        else:
            print(f"✗ Configuration file {f} missing")

    print("Linting setup complete.")

if __name__ == "__main__":
    main()