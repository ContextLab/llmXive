import os
import sys
import venv
import subprocess
from pathlib import Path
import logging

# Ensure we can import the project's logging utilities if they exist in the path
# The project structure places utils in code/utils, but for setup scripts running
# from the root or code/, we ensure the path is correct.
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.logging import get_logger
except ImportError:
    # Fallback if logging module isn't set up yet (which is expected for T004)
    # We configure a basic logger to ensure T004 can run independently.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger("setup_venv")

def setup_venv(project_path: str, venv_name: str = "venv") -> bool:
    """
    Creates a Python virtual environment in the specified project path.

    Args:
        project_path: The root directory of the project where the venv will be created.
        venv_name: The name of the virtual environment directory (default: 'venv').

    Returns:
        bool: True if successful, False otherwise.
    """
    target_path = Path(project_path) / venv_name

    if target_path.exists():
        logger.warning(f"Virtual environment already exists at {target_path}. Skipping creation.")
        return True

    logger.info(f"Creating virtual environment at {target_path}...")
    try:
        venv.create(str(target_path), with_pip=True)
        
        # Verify creation by checking for activation scripts and python executable
        if sys.platform == "win32":
            python_exec = target_path / "Scripts" / "python.exe"
            pip_exec = target_path / "Scripts" / "pip.exe"
        else:
            python_exec = target_path / "bin" / "python"
            pip_exec = target_path / "bin" / "pip"

        if not python_exec.exists() or not pip_exec.exists():
            logger.error("Virtual environment created but verification failed (missing python or pip).")
            return False

        logger.info("Virtual environment created successfully.")
        
        # Optional: Upgrade pip to latest version to ensure compatibility
        logger.info("Upgrading pip...")
        subprocess.run(
            [str(python_exec), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upgrade pip: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False

def main():
    """
    Main entry point for the virtual environment setup script.
    Expects the project root path as a command-line argument or uses current directory.
    """
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        # Default to the directory containing this script's parent (project root)
        # Since this file is at code/setup_venv.py, parent is project root
        project_path = str(Path(__file__).parent.parent)

    logger.info(f"Starting venv setup for project at: {project_path}")
    
    success = setup_venv(project_path)
    
    if success:
        logger.info("Task T004 completed: Python virtual environment created.")
        sys.exit(0)
    else:
        logger.error("Task T004 failed: Could not create Python virtual environment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
