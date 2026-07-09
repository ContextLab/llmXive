"""
Module to handle virtual environment creation and dependency installation.
"""
import os
import subprocess
import sys
from pathlib import Path

def create_venv(venv_path: str = "venv") -> bool:
    """
    Creates a Python virtual environment at the specified path.
    
    Args:
        venv_path: Path where the virtual environment will be created.
        
    Returns:
        True if successful, False otherwise.
    """
    venv_dir = Path(venv_path)
    if venv_dir.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return True
    
    try:
        print(f"Creating virtual environment at {venv_path}...")
        result = subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
            capture_output=True,
            text=True
        )
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e.stderr}")
        return False

def install_dependencies(venv_path: str = "venv", requirements_path: str = "requirements.txt") -> bool:
    """
    Installs dependencies from requirements.txt into the virtual environment.
    
    Args:
        venv_path: Path to the virtual environment.
        requirements_path: Path to the requirements.txt file.
        
    Returns:
        True if successful, False otherwise.
    """
    venv_dir = Path(venv_path)
    req_file = Path(requirements_path)
    
    if not venv_dir.exists():
        print(f"Error: Virtual environment not found at {venv_path}.")
        return False
    
    if not req_file.exists():
        print(f"Error: Requirements file not found at {requirements_path}.")
        return False
    
    # Determine the pip executable path based on OS
    if os.name == 'nt':  # Windows
        pip_executable = venv_dir / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        pip_executable = venv_dir / "bin" / "pip"
    
    if not pip_executable.exists():
        print(f"Error: pip executable not found at {pip_executable}.")
        return False
    
    try:
        print(f"Installing dependencies from {requirements_path}...")
        result = subprocess.run(
            [str(pip_executable), "install", "-r", requirements_path],
            check=True,
            capture_output=True,
            text=True
        )
        print("Dependencies installed successfully.")
        print("Installation log:")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e.stderr}")
        return False

def main():
    """Main entry point for setting up the environment."""
    print("Starting project environment setup...")
    
    venv_path = "venv"
    requirements_path = "requirements.txt"
    
    # Step 1: Create virtual environment
    if not create_venv(venv_path):
        print("Failed to create virtual environment. Aborting.")
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies(venv_path, requirements_path):
        print("Failed to install dependencies. Aborting.")
        sys.exit(1)
    
    print("Environment setup completed successfully.")
    print(f"Activate the environment and run your scripts.")
    if os.name == 'nt':
        print(f"Activation command: {venv_path}\\Scripts\\activate.bat")
    else:
        print(f"Activation command: source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()
