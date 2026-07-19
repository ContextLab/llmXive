"""
Script to initialize the Git repository and Python virtual environment.

This script performs the following actions:
1. Initializes a Git repository if one does not exist.
2. Creates a Python virtual environment (venv) in the project root.
3. Installs dependencies from requirements.txt into the virtual environment.

Usage:
    python code/scripts/init_env.py
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a shell command and print it."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=cwd, check=check, shell=False)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        raise

def init_git():
    """Initialize git repository if not already initialized."""
    if (Path(".git")).exists():
        print("Git repository already exists.")
        return
    
    print("Initializing Git repository...")
    run_command(["git", "init"])
    run_command(["git", "config", "user.name", "llmXive-bot"])
    run_command(["git", "config", "user.email", "bot@llmxive.ai"])
    print("Git repository initialized.")

def create_venv():
    """Create virtual environment if it does not exist."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("Virtual environment 'venv' already exists.")
    else:
        print("Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", "venv"])
        print("Virtual environment created.")

def install_dependencies():
    """Install dependencies from requirements.txt."""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("Warning: requirements.txt not found. Skipping dependency installation.")
        return

    venv_python = Path("venv/bin/python") if os.name != "nt" else Path("venv\\Scripts\\python.exe")
    
    if not venv_python.exists():
        print("Error: Virtual environment not found. Run init_env.py again.")
        sys.exit(1)

    print("Installing dependencies...")
    run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
    run_command([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed.")

def main():
    print("Starting project environment initialization...")
    init_git()
    create_venv()
    install_dependencies()
    print("Initialization complete.")

if __name__ == "__main__":
    main()