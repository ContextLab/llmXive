"""
Setup script to create a Python 3.11 virtual environment and install dependencies.

This script:
1. Checks for Python 3.11 availability.
2. Creates a virtual environment in 'code/venv'.
3. Upgrades pip.
4. Installs dependencies from 'code/requirements.txt'.
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

def check_python_version():
    """Verify that the running Python interpreter is 3.11."""
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        print(f"ERROR: Python 3.11 is required. Found Python {version.major}.{version.minor}")
        print("Please install Python 3.11 and ensure it is available as 'python3.11' or 'python'.")
        sys.exit(1)
    print(f"✓ Python version check passed: {sys.version}")

def create_virtual_environment(venv_path: Path):
    """Create a virtual environment at the specified path."""
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing...")
        shutil.rmtree(venv_path)
    
    print(f"Creating virtual environment at {venv_path}...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    print("✓ Virtual environment created.")

def install_dependencies(venv_path: Path, requirements_path: Path):
    """Upgrade pip and install dependencies from requirements.txt."""
    venv_bin = venv_path / "bin" if os.name != "nt" else venv_path / "Scripts"
    pip_executable = venv_bin / "pip"
    
    if not pip_executable.exists():
        print(f"ERROR: pip not found at {pip_executable}")
        sys.exit(1)

    print("Upgrading pip...")
    subprocess.run([str(pip_executable), "install", "--upgrade", "pip"], check=True)

    print(f"Installing dependencies from {requirements_path}...")
    result = subprocess.run(
        [str(pip_executable), "install", "-r", str(requirements_path)],
        check=True
    )
    print("✓ Dependencies installed successfully.")

def main():
    project_root = Path(__file__).parent
    requirements_file = project_root / "requirements.txt"
    venv_dir = project_root / "venv"

    if not requirements_file.exists():
        print(f"ERROR: requirements.txt not found at {requirements_file}")
        sys.exit(1)

    check_python_version()
    create_virtual_environment(venv_dir)
    install_dependencies(venv_dir, requirements_file)

    print("\n" + "="*50)
    print("Setup complete!")
    print(f"To activate the environment, run:")
    if os.name == "nt":
        print(f"  {venv_dir}\\Scripts\\activate.bat")
    else:
        print(f"  source {venv_dir}/bin/activate")
    print("="*50)

if __name__ == "__main__":
    main()