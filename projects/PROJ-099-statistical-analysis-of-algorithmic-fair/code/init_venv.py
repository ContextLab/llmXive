"""
Initialize a Python virtual environment for the PROJ-099 project.

This script creates a virtual environment in the project root and installs
all dependencies from requirements.txt.

Usage:
    python code/init_venv.py

After running, activate the environment with:
    source venv/bin/activate  # On Unix/macOS
    venv\\Scripts\\activate   # On Windows
"""
import os
import subprocess
import sys
from pathlib import Path

def create_virtual_environment(venv_path: Path) -> bool:
    """
    Create a Python virtual environment at the specified path.

    Args:
        venv_path: Path where the virtual environment should be created.

    Returns:
        True if creation was successful, False otherwise.
    """
    try:
        print(f"Creating virtual environment at: {venv_path}")
        subprocess.check_call(
            [sys.executable, "-m", "venv", str(venv_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error creating virtual environment: {e}")
        return False

def install_dependencies(venv_path: Path, requirements_path: Path) -> bool:
    """
    Install dependencies from requirements.txt into the virtual environment.

    Args:
        venv_path: Path to the virtual environment.
        requirements_path: Path to requirements.txt.

    Returns:
        True if installation was successful, False otherwise.
    """
    try:
        # Determine pip path based on OS
        if sys.platform == "win32":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"

        print(f"Installing dependencies from: {requirements_path}")
        subprocess.check_call(
            [str(pip_path), "install", "-r", str(requirements_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error installing dependencies: {e}")
        return False

def verify_installation(venv_path: Path) -> bool:
    """
    Verify that key packages were installed successfully.

    Args:
        venv_path: Path to the virtual environment.

    Returns:
        True if verification passed, False otherwise.
    """
    try:
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            python_path = venv_path / "bin" / "python"

        packages = ["scikit_learn", "statsmodels", "pandas", "numpy", "scipy"]
        for package in packages:
            result = subprocess.run(
                [str(python_path), "-c", f"import {package}"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Warning: Package {package} may not be installed correctly")
                return False

        print("All key packages verified successfully.")
        return True
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

def main() -> int:
    """
    Main entry point for virtual environment initialization.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    print("=" * 60)
    print("PROJ-099 Virtual Environment Initialization")
    print("=" * 60)

    # Check if requirements.txt exists
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        print("Please ensure requirements.txt exists before running this script.")
        return 1

    # Create virtual environment
    if not create_virtual_environment(venv_path):
        print("Failed to create virtual environment.")
        return 1

    # Install dependencies
    if not install_dependencies(venv_path, requirements_path):
        print("Failed to install dependencies.")
        return 1

    # Verify installation
    if not verify_installation(venv_path):
        print("Warning: Package verification failed, but installation may have succeeded.")

    print("=" * 60)
    print("Virtual environment setup complete!")
    print("=" * 60)
    print(f"\nTo activate the environment:")
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())