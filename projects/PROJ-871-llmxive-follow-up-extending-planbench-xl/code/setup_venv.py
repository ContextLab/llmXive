import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    """Return the root directory of the project."""
    # The script is expected to be run from the project root or code/
    # We look for the requirements.txt in the parent of code/
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    return project_root

def main():
    """
    Initialize a Python virtual environment and install dependencies.
    
    This script:
    1. Checks if a virtual environment exists at `venv/`.
    2. If not, creates one.
    3. Activates it and installs packages from `requirements.txt`.
    4. Logs the action to `data/logs/setup.log`.
    """
    project_root = get_project_root()
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"
    log_dir = project_root / "data" / "logs"
    log_path = log_dir / "setup.log"

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"Project Root: {project_root}")
    print(f"Virtual Environment Path: {venv_path}")
    print(f"Requirements Path: {requirements_path}")

    if not requirements_path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {requirements_path}")

    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create virtual environment: {e}")
    else:
        print("Virtual environment already exists.")

    # Determine the python executable inside the venv
    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
        pip_executable = venv_path / "Scripts" / "pip.exe"
    else:
        python_executable = venv_path / "bin" / "python"
        pip_executable = venv_path / "bin" / "pip"

    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.check_call([str(python_executable), "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to upgrade pip: {e}")

    # Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.check_call([str(pip_executable), "install", "-r", str(requirements_path)])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to install dependencies: {e}")

    # Log success
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} - Virtual environment initialized and dependencies installed successfully.\n"
    with open(log_path, "a") as f:
        f.write(log_entry)
    
    print("Setup complete. Activate the environment with:")
    if sys.platform == "win32":
        print(f"  venv\\Scripts\\activate")
    else:
        print(f"  source venv/bin/activate")

if __name__ == "__main__":
    main()