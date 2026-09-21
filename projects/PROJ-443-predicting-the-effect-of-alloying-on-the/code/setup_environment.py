"""
Environment setup script for the HEA Elastic Modulus Prediction project.
Verifies Python version, installs dependencies, and creates directory structure.
"""
import os
import subprocess
import sys
from pathlib import Path
import argparse

MIN_PYTHON_VERSION = (3, 11)
REQUIRED_PACKAGES = [
    "pandas>=2.0",
    "scikit-learn>=1.3",
    "numpy>=1.24",
    "requests>=2.31",
    "pyyaml>=6.0",
    "shap>=0.44",
    "scipy>=1.11",
    "pymatgen>=2023.10.10",
    "pytest>=7.4",
]

def verify_python_version():
    """Verify that the current Python version meets the minimum requirement."""
    current_version = sys.version_info[:2]
    if current_version < MIN_PYTHON_VERSION:
        required = ".".join(map(str, MIN_PYTHON_VERSION))
        current = ".".join(map(str, current_version))
        raise RuntimeError(
            f"Python version {current} is not supported. "
            f"Python {required} or higher is required."
        )
    print(f"✓ Python version verified: {sys.version}")

def create_directories():
    """Create the required project directory structure."""
    root = Path(__file__).resolve().parent.parent
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/external",
        "results",
        "figures",
        "code/utils",
        "code/data",
        "code/features",
        "code/models",
        "code/eval",
        "code/interpret",
        "code/report",
        "code/pipeline",
        "code/tests/unit",
        "code/tests/integration",
    ]

    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Ensure __init__.py exists for Python packages
        if "code" in dir_path or "src" in dir_path or "tests" in dir_path:
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"  Created {init_file}")

    print(f"✓ Directory structure created in {root}")

def install_dependencies():
    """Install project dependencies from requirements.txt."""
    root = Path(__file__).resolve().parent.parent
    requirements_file = root / "requirements.txt"

    if not requirements_file.exists():
        print("⚠ requirements.txt not found. Skipping dependency installation.")
        print("  Please run: pip install -r requirements.txt")
        return False

    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        print("  Please install manually: pip install -r requirements.txt")
        return False

def main():
    """Main entry point for environment setup."""
    parser = argparse.ArgumentParser(
        description="Setup the HEA Elastic Modulus Prediction project environment."
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation"
    )
    parser.add_argument(
        "--no-dirs",
        action="store_true",
        help="Skip directory creation"
    )
    args = parser.parse_args()

    try:
        verify_python_version()
    except RuntimeError as e:
        print(f"✗ {e}")
        sys.exit(1)

    if not args.no_dirs:
        create_directories()

    if not args.skip_install:
        install_dependencies()

    print("\n✓ Project environment setup complete!")
    print("  Next steps:")
    print("  1. Activate virtual environment (if using one)")
    print("  2. Run: pre-commit install (if using pre-commit)")
    print("  3. Start implementing tasks from tasks.md")

if __name__ == "__main__":
    main()