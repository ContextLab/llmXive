"""
Setup script for PROJ-443: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys.

This script initializes the Python 3.11 project environment by:
1. Verifying the Python version is 3.11.x
2. Installing required dependencies from requirements.txt
3. Creating necessary directory structure if not present
"""
import os
import subprocess
import sys
from pathlib import Path

# Define project root relative to this script location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to ensure exist (per T002 plan)
REQUIRED_DIRS = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "results",
    "code",
    "code/utils",
    "code/data",
    "code/features",
    "code/model",
    "code/eval",
    "code/interpret",
    "code/report",
    "code/pipeline",
    "specs"
]

def verify_python_version():
    """Verify Python version is 3.11.x."""
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        print(f"ERROR: Python 3.11 is required. Found Python {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"✓ Python version verified: {sys.version}")

def install_dependencies():
    """Install dependencies from requirements.txt."""
    requirements_path = PROJECT_ROOT / "requirements.txt"
    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)
    
    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path), "--quiet"
        ])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create required directory structure."""
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(PROJECT_ROOT)}")
        else:
            print(f"Directory exists: {full_path.relative_to(PROJECT_ROOT)}")

def main():
    """Main entry point for setup."""
    print("=== PROJ-443 Environment Setup ===")
    verify_python_version()
    install_dependencies()
    create_directories()
    print("=== Setup Complete ===")

if __name__ == "__main__":
    main()