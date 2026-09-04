"""
Script to install project dependencies from requirements.txt.
This script is the implementation of task T005b.
"""
import os
import sys
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_dependencies(venv_path: Path, requirements_path: Path) -> bool:
    """
    Install dependencies from requirements.txt into the virtual environment.

    Args:
        venv_path: Path to the virtual environment directory
        requirements_path: Path to the requirements.txt file

    Returns:
        bool: True if installation was successful, False otherwise
    """
    if not venv_path.exists():
        logger.error(f"Virtual environment not found at: {venv_path}")
        return False

    if not requirements_path.exists():
        logger.error(f"Requirements file not found at: {requirements_path}")
        return False

    # Determine the pip executable path based on OS
    if sys.platform == 'win32':
        pip_path = venv_path / 'Scripts' / 'pip.exe'
    else:
        pip_path = venv_path / 'bin' / 'pip'

    if not pip_path.exists():
        logger.error(f"pip executable not found at: {pip_path}")
        return False

    logger.info(f"Installing dependencies from {requirements_path}...")
    logger.info(f"Using pip at: {pip_path}")

    try:
        result = subprocess.run(
            [str(pip_path), 'install', '-r', str(requirements_path)],
            check=True,
            capture_output=False,
            text=True
        )
        logger.info("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        logger.error(f"Return code: {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during dependency installation: {e}")
        return False

def main():
    """Main entry point for the dependency installation script."""
    # Determine project root based on script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    venv_path = project_root / 'venv'
    requirements_path = project_root / 'code' / 'requirements.txt'

    logger.info(f"Project root: {project_root}")
    logger.info(f"Virtual environment path: {venv_path}")
    logger.info(f"Requirements file path: {requirements_path}")

    success = install_dependencies(venv_path, requirements_path)

    if success:
        logger.info("Task T005b completed successfully.")
        sys.exit(0)
    else:
        logger.error("Task T005b failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()