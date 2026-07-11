"""
Script to verify the Python environment and dependencies for the project.
This script checks:
1. Python version (>= 3.11)
2. Installs dependencies from requirements.txt if not already installed
3. Runs `pip check` to verify no dependency conflicts
"""
import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Verify Python version is 3.11 or higher."""
    version = sys.version_info
    print(f"Detected Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("ERROR: Python 3.11 or higher is required.")
        sys.exit(1)
    print("✓ Python version check passed.")

def install_dependencies():
    """Install dependencies from code/requirements.txt."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    if not requirements_path.exists():
        print("ERROR: requirements.txt not found.")
        sys.exit(1)
    
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
        print("✓ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

def run_pip_check():
    """Run pip check to verify no dependency conflicts."""
    print("Running pip check to verify dependency consistency...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            print("✓ pip check output:")
            print(result.stdout)
        else:
            print("✓ pip check passed with no output (all dependencies satisfied).")
    except subprocess.CalledProcessError as e:
        print("ERROR: pip check failed - dependency conflicts detected:")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

def main():
    """Main entry point for environment verification."""
    print("=" * 60)
    print("Verifying Project Environment")
    print("=" * 60)
    
    check_python_version()
    install_dependencies()
    run_pip_check()
    
    print("=" * 60)
    print("Environment verification completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()