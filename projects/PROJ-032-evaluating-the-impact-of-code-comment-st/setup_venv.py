"""
Script to initialize the Python 3.9+ virtual environment and install dependencies.
Corresponds to Task T002: Initialize Python 3.9+ project.

Usage:
    python setup_venv.py
"""
import subprocess
import sys
import os
import venv
import shutil

def run_command(cmd, check=True):
    """Run a shell command and print output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if not check:
            return False
        raise
    return True

def main():
    # 1. Create virtual environment
    print("Creating virtual environment 'venv'...")
    venv_path = "venv"
    if os.path.exists(venv_path):
        print(f"Virtual environment '{venv_path}' already exists. Skipping creation.")
    else:
        venv.create(venv_path, with_pip=True)
        print("Virtual environment created successfully.")

    # Determine the path to the pip executable in the venv
    if sys.platform == "win32":
        pip_executable = os.path.join(venv_path, "Scripts", "pip")
        python_executable = os.path.join(venv_path, "Scripts", "python")
    else:
        pip_executable = os.path.join(venv_path, "bin", "pip")
        python_executable = os.path.join(venv_path, "bin", "python")

    # 2. Upgrade pip
    print("Upgrading pip...")
    run_command([python_executable, "-m", "pip", "install", "--upgrade", "pip"])

    # 3. Install runtime dependencies
    print("\nInstalling runtime dependencies from requirements.txt...")
    if os.path.exists("requirements.txt"):
        run_command([pip_executable, "install", "-r", "requirements.txt"])
    else:
        print("Warning: requirements.txt not found. Skipping runtime install.")

    # 4. Install development dependencies
    print("\nInstalling development dependencies from dev-requirements.txt...")
    if os.path.exists("dev-requirements.txt"):
        run_command([pip_executable, "install", "-r", "dev-requirements.txt"])
    else:
        print("Warning: dev-requirements.txt not found. Skipping dev install.")

    print("\nProject initialization complete.")
    print(f"Activate the environment with: source {venv_path}/bin/activate (Unix) or {venv_path}\\Scripts\\activate (Windows)")

if __name__ == "__main__":
    main()