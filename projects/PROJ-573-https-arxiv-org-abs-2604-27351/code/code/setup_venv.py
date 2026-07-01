"""
Standalone script to create and initialize the virtual environment.
This is a simplified version for quick setup.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def main():
    """Create virtual environment and install basic dependencies."""
    venv_path = Path("code/.venv")
    
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        print("To reinstall, remove the directory first: rm -rf code/.venv")
        return
    
    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    print("✓ Virtual environment created")
    
    # Upgrade pip
    pip_path = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip"
    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
    print("✓ Pip upgraded")
    
    # Install requirements if available
    requirements_path = Path("code/requirements.txt")
    if requirements_path.exists():
        print(f"Installing dependencies from {requirements_path}...")
        subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], check=True)
        print("✓ Dependencies installed")
    else:
        print("WARNING: requirements.txt not found. Install dependencies manually.")
    
    print(f"\nTo activate the environment:")
    if os.name == "nt":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()
