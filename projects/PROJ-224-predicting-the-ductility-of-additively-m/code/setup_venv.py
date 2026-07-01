import os
import subprocess
import sys
import venv
from pathlib import Path

def check_python_version():
    """
    Check if the current Python version is 3.11.
    Returns True if 3.11.x, False otherwise.
    """
    version = sys.version_info
    if version.major == 3 and version.minor == 11:
        return True
    return False

def main():
    """
    Initialize a Python 3.11 virtual environment in the 'venv' directory
    at the project root.
    
    If the environment already exists, it will be skipped.
    If the Python version is not 3.11, a warning is logged and the task fails.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "venv"

    if venv_path.exists():
        logger.info(f"Virtual environment already exists at {venv_path}. Skipping initialization.")
        return

    if not check_python_version():
        logger.error(f"Current Python version is {sys.version}. This task requires Python 3.11.")
        logger.error("Please ensure Python 3.11 is installed and active in the environment running this script.")
        sys.exit(1)

    logger.info(f"Initializing Python 3.11 virtual environment at {venv_path}...")
    
    try:
        venv.create(venv_path, with_pip=True)
        logger.info("Virtual environment created successfully.")
        
        # Verify the interpreter version inside the venv
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        result = subprocess.run([str(python_exe), "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Verified venv Python version: {result.stdout.strip()}")
        else:
            logger.warning("Could not verify venv Python version.")
            
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
