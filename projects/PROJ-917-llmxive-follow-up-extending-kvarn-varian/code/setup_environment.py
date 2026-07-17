"""
Environment setup and validation for the llmXive project.
Ensures Python version compatibility and verifies critical dependencies.
"""
import sys
import importlib
import subprocess
from pathlib import Path

REQUIRED_VERSION = (3, 11)
MIN_VERSION = (3, 11, 0)
MAX_VERSION = (3, 12, 0)  # Exclusive upper bound

def check_python_version():
    """Verify the running Python version matches project requirements."""
    current = sys.version_info[:3]
    if current < MIN_VERSION or current >= MAX_VERSION:
        print(f"ERROR: Python version {sys.version} is not supported.")
        print(f"Required: Python >= {MIN_VERSION[0]}.{MIN_VERSION[1]}.{MIN_VERSION[2]} "
              f"and < {MAX_VERSION[0]}.{MAX_VERSION[1]}.{MAX_VERSION[2]}")
        sys.exit(1)
    print(f"✓ Python version check passed: {sys.version.split()[0]}")

def check_dependencies():
    """Verify that all required packages from requirements.txt are installed."""
    # Read requirements to get list of packages (ignoring flags and URLs)
    req_path = Path(__file__).parent.parent / "requirements.txt"
    if not req_path.exists():
        print(f"WARNING: {req_path} not found. Skipping dependency check.")
        return

    packages = []
    with open(req_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Handle --index-url and other flags
            if line.startswith("-"):
                continue
            # Strip version specifiers to get package name
            pkg_name = line.split(">=")[0].split("<")[0].split("[")[0].strip()
            if pkg_name:
                packages.append(pkg_name)

    missing = []
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"ERROR: Missing dependencies: {missing}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

    print(f"✓ All {len(packages)} required dependencies verified.")

def main():
    """Main entry point for environment validation."""
    print("Running project environment validation...")
    check_python_version()
    check_dependencies()
    print("Environment validation complete. Ready to run experiments.")

if __name__ == "__main__":
    main()
