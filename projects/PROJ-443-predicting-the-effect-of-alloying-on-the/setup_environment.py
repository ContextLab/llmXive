"""
Project Environment Setup Script.
Verifies Python version, creates directory structure, and installs dependencies.
"""
import os
import subprocess
import sys
from pathlib import Path
import argparse

REQUIRED_PYTHON_VERSION = (3, 11)

def verify_python_version():
    """Check if current Python version is 3.11 or higher."""
    if sys.version_info < REQUIRED_PYTHON_VERSION:
        print(f"ERROR: Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}+ is required. "
              f"Current version: {sys.version}")
        sys.exit(1)
    print(f"Python version verified: {sys.version}")

def create_directories():
    """Create the standard project directory structure."""
    base_dir = Path(__file__).parent
    dirs = [
        base_dir / "code" / "src",
        base_dir / "code" / "tests",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "results",
        base_dir / "figures",
        base_dir / "code" / "utils",
        base_dir / "code" / "models",
        base_dir / "code" / "features",
        base_dir / "code" / "pipeline",
        base_dir / "code" / "eval",
        base_dir / "code" / "interpret",
        base_dir / "code" / "report",
        base_dir / "code" / "data",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"Created {len(dirs)} directories under {base_dir}")

def install_dependencies():
    """Install dependencies from requirements.txt."""
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        print("WARNING: requirements.txt not found. Skipping dependency installation.")
        return

    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(req_file), "--upgrade"
        ])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Initialize HEA Project Environment")
    parser.add_argument("--skip-install", action="store_true", help="Skip pip install")
    parser.add_argument("--skip-dirs", action="store_true", help="Skip directory creation")
    args = parser.parse_args()

    verify_python_version()

    if not args.skip_dirs:
        create_directories()

    if not args.skip_install:
        install_dependencies()

    print("Project environment setup complete.")

if __name__ == "__main__":
    main()
