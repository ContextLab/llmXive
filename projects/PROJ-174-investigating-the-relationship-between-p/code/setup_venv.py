"""
Script to setup a Python 3.11 virtual environment in the code/ directory
and install dependencies from requirements.txt.
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python 3.11 is available."""
    try:
        result = subprocess.run(
            [sys.executable, '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        version_str = result.stdout
        # Check for Python 3.11
        if '3.11' not in version_str:
            print(f"Warning: Current Python version is {version_str.strip()}, but 3.11 is preferred.")
            print("Attempting to proceed anyway...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error checking Python version: {e}")
        return False

def create_virtual_environment(venv_path):
    """Create a virtual environment in the specified path."""
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing...")
        shutil.rmtree(venv_path)

    print(f"Creating virtual environment at {venv_path}...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'venv', str(venv_path)],
            check=True
        )
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False

def install_dependencies(venv_path, requirements_path):
    """Install dependencies from requirements.txt into the virtual environment."""
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False

    # Determine the pip path
    if os.system == 'win':
        pip_path = venv_path / 'Scripts' / 'pip.exe'
    else:
        pip_path = venv_path / 'bin' / 'pip'

    if not pip_path.exists():
        print(f"Error: pip not found at {pip_path}")
        return False

    print(f"Installing dependencies from {requirements_path}...")
    try:
        # Upgrade pip first
        subprocess.run(
            [str(pip_path), 'install', '--upgrade', 'pip'],
            check=True
        )
        # Install requirements
        subprocess.run(
            [str(pip_path), 'install', '-r', str(requirements_path)],
            check=True
        )
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def main():
    """Main function to setup the virtual environment."""
    print("Setting up Python 3.11 virtual environment...")

    # Check Python version
    if not check_python_version():
        print("Failed to verify Python version. Exiting.")
        sys.exit(1)

    # Define paths
    project_root = Path(__file__).resolve().parent
    venv_path = project_root / 'venv'
    requirements_path = project_root / 'requirements.txt'

    # Create virtual environment
    if not create_virtual_environment(venv_path):
        print("Failed to create virtual environment. Exiting.")
        sys.exit(1)

    # Install dependencies
    if not install_dependencies(venv_path, requirements_path):
        print("Failed to install dependencies. Exiting.")
        sys.exit(1)

    print("Setup complete! Activate the environment with:")
    if os.system == 'win':
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")

if __name__ == '__main__':
    main()
