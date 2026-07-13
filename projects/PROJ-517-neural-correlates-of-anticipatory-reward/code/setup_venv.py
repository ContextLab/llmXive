import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Initialize a virtual environment in the project root (.venv)
    and install dependencies from requirements.txt.
    
    This script handles the entire setup process:
    1. Creates .venv directory using python -m venv
    2. Activates the virtual environment
    3. Installs all packages listed in requirements.txt
    """
    project_root = Path(__file__).parent.parent
    venv_path = project_root / ".venv"
    requirements_path = project_root / "projects" / "PROJ-517-neural-correlates-of-anticipatory-reward" / "requirements.txt"
    
    # Check if requirements.txt exists
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print(f"Error: Python 3.10+ is required. Current version: {sys.version}")
        sys.exit(1)
    
    print(f"Setting up virtual environment at: {venv_path}")
    
    # Step 1: Create virtual environment
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✓ Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e.stderr.decode()}")
        sys.exit(1)
    
    # Determine the path to pip in the virtual environment
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    if not pip_path.exists():
        print(f"Error: pip not found at {pip_path}")
        sys.exit(1)
    
    # Step 2: Upgrade pip
    print("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✓ pip upgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not upgrade pip: {e.stderr.decode()}")
    
    # Step 3: Install requirements
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e.stderr.decode()}")
        sys.exit(1)
    
    print("\nVirtual environment setup complete!")
    print(f"To activate, run: source .venv/bin/activate (Linux/Mac) or .venv\\Scripts\\activate (Windows)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
