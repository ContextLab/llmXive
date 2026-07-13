"""
Task T002b: Set up Python virtual environment and install requirements.

This script programmatically creates a virtual environment named 'venv'
in the project root and installs all dependencies listed in 'requirements.txt'.
It uses the subprocess module to invoke the standard library's venv module
and pip, ensuring the environment is isolated and dependencies are resolved.
"""
import subprocess
import sys
import os
import shutil

VENV_DIR = "venv"
REQUIREMENTS_FILE = "requirements.txt"

def main():
    # Check if requirements.txt exists
    if not os.path.exists(REQUIREMENTS_FILE):
        print(f"Error: {REQUIREMENTS_FILE} not found in current directory.")
        sys.exit(1)

    # Remove existing venv if present to ensure a clean slate
    if os.path.exists(VENV_DIR):
        print(f"Removing existing {VENV_DIR} directory...")
        shutil.rmtree(VENV_DIR)

    # Create the virtual environment
    print(f"Creating virtual environment in {VENV_DIR}...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

    # Determine the path to the pip executable inside the venv
    if os.name == "nt":  # Windows
        pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
        python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:  # Unix/Linux/Mac
        pip_path = os.path.join(VENV_DIR, "bin", "pip")
        python_path = os.path.join(VENV_DIR, "bin", "python")

    # Upgrade pip inside the venv
    print("Upgrading pip...")
    try:
        subprocess.check_call([python_path, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to upgrade pip: {e}")
        # Continue anyway, as install might still work

    # Install requirements
    print(f"Installing requirements from {REQUIREMENTS_FILE}...")
    try:
        subprocess.check_call([pip_path, "install", "-r", REQUIREMENTS_FILE])
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)

    print(f"Virtual environment setup complete. Activate with:")
    if os.name == "nt":
        print(f"    {VENV_DIR}\\Scripts\\activate")
    else:
        print(f"    source {VENV_DIR}/bin/activate")

if __name__ == "__main__":
    main()