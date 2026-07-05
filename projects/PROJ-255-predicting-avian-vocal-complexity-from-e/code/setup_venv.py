import os
import subprocess
import sys
import shutil
from pathlib import Path

def get_python_executable():
    """Get the current Python executable path."""
    return sys.executable

def run_command(command, cwd=None, check=True):
    """Run a shell command and raise on failure."""
    try:
        subprocess.run(command, shell=True, check=check, cwd=cwd)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {command}") from e

def setup_venv(project_root):
    """Create a virtual environment in the project root if it doesn't exist."""
    venv_path = project_root / "venv"
    if venv_path.exists():
        # Clean existing venv to ensure fresh install
        shutil.rmtree(venv_path)
    
    python_exe = get_python_executable()
    run_command(f"{python_exe} -m venv {venv_path}")
    return venv_path

def activate_and_upgrade_pip(venv_path):
    """Activate venv (conceptually) and upgrade pip."""
    if os.name == 'nt':
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Upgrade pip using the venv python directly
    run_command(f"{python_path} -m pip install --upgrade pip")
    return pip_path

def install_requirements(pip_path, requirements_path):
    """Install dependencies from requirements.txt."""
    if not requirements_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
    
    run_command(f"{pip_path} install -r {requirements_path}")

def main():
    """Main entry point to setup virtual environment and install dependencies."""
    # Determine project root (assuming script is in code/ relative to root)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    print(f"Project root detected at: {project_root}")
    
    # 1. Setup Virtual Environment
    print("Creating virtual environment...")
    venv_path = setup_venv(project_root)
    print(f"Virtual environment created at: {venv_path}")
    
    # 2. Get Pip path
    pip_path = activate_and_upgrade_pip(venv_path)
    print(f"Pip path: {pip_path}")
    
    # 3. Install Requirements
    requirements_path = project_root / "requirements.txt"
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)
        
    print(f"Installing dependencies from {requirements_path}...")
    install_requirements(pip_path, requirements_path)
    print("Dependencies installed successfully.")
    
    # Create a marker file to indicate setup completion
    marker = venv_path / "setup_complete.txt"
    marker.write_text("Setup completed successfully.\n")
    print(f"Setup marker created at: {marker}")

if __name__ == "__main__":
    main()
