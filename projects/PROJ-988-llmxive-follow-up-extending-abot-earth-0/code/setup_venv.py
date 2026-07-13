import os
import subprocess
import sys
import venv
from pathlib import Path
import logging

# Configure logging for the setup process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup_venv")

def main():
    """
    Initialize a Python 3.11 virtual environment and install dependencies.
    
    This script:
    1. Checks for Python 3.11 availability.
    2. Creates a virtual environment in 'code/.venv'.
    3. Upgrades pip.
    4. Installs dependencies from 'code/requirements.txt'.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    venv_path = code_dir / ".venv"
    requirements_path = code_dir / "requirements.txt"

    # Ensure code directory exists
    code_dir.mkdir(parents=True, exist_ok=True)

    # Check Python version
    python_version = sys.version_info
    if python_version.major != 3 or python_version.minor < 11:
        logger.warning(f"Current Python version is {sys.version}. "
                       f"Attempting to create venv, but Python 3.11+ is recommended.")
    
    # Check if venv already exists
    if venv_path.exists() and (venv_path / "pyvenv.cfg").exists():
        logger.info(f"Virtual environment already exists at {venv_path}. Reusing.")
    else:
        logger.info(f"Creating virtual environment at {venv_path}...")
        try:
            venv.create(venv_path, with_pip=True)
            logger.info("Virtual environment created successfully.")
        except Exception as e:
            logger.error(f"Failed to create virtual environment: {e}")
            sys.exit(1)

    # Determine the path to the pip executable within the venv
    if sys.platform == "win32":
        pip_executable = venv_path / "Scripts" / "pip.exe"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"

    if not pip_executable.exists():
        logger.error(f"Pip executable not found at {pip_executable}.")
        sys.exit(1)

    # Upgrade pip
    logger.info("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"],
            check=True
        )
        logger.info("Pip upgraded successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upgrade pip: {e}")
        sys.exit(1)

    # Install dependencies
    if requirements_path.exists():
        logger.info(f"Installing dependencies from {requirements_path}...")
        try:
            subprocess.run(
                [str(pip_executable), "install", "-r", str(requirements_path)],
                check=True
            )
            logger.info("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            sys.exit(1)
    else:
        logger.warning(f"Requirements file not found at {requirements_path}. Skipping installation.")

    logger.info("Setup complete.")

if __name__ == "__main__":
    main()
