import subprocess
import sys
import os
import shutil
from pathlib import Path

def check_python_version():
    """Check if the current Python version is 3.11."""
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        print(f"Error: Python 3.11 is required. Found {version.major}.{version.minor}.{version.micro}")
        return False
    return True

def create_venv(venv_path: Path):
    """Create a virtual environment at the specified path."""
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing...")
        shutil.rmtree(venv_path)
    
    print(f"Creating virtual environment at {venv_path}...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}")
        return False
    return True

def activate_and_install(venv_path: Path, requirements_path: Path):
    """Activate the virtual environment and install dependencies."""
    if not venv_path.exists():
        print(f"Error: Virtual environment not found at {venv_path}")
        return False

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False

    # Determine the correct pip path based on OS
    if os.name == 'nt':
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"

    if not pip_path.exists():
        print(f"Error: pip not found at {pip_path}")
        return False

    print("Upgrading pip...")
    try:
        subprocess.check_call([str(pip_path), "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to upgrade pip: {e}")
        return False

    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.check_call([str(pip_path), "install", "-r", str(requirements_path)])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False
    
    return True

def main():
    """Main entry point for setting up the virtual environment."""
    project_root = Path(__file__).resolve().parent.parent.parent
    venv_path = project_root / "code" / "venv"
    requirements_path = project_root / "requirements.txt"

    print(f"Project root: {project_root}")
    print(f"Virtual environment path: {venv_path}")
    print(f"Requirements path: {requirements_path}")

    if not check_python_version():
        sys.exit(1)

    if not create_venv(venv_path):
        sys.exit(1)

    if not activate_and_install(venv_path, requirements_path):
        sys.exit(1)

    print("Setup complete. To activate the environment, run:")
    if os.name == 'nt':
        print(f"  code\\venv\\Scripts\\activate.bat")
    else:
        print(f"  source code/venv/bin/activate")

if __name__ == "__main__":
    main()