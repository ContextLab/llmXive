"""
Task T002a: Create Python 3.11 virtual environment.

This script creates a virtual environment in the project root `venv/` directory.
It verifies that the Python version used to create the environment is 3.11.x.
If the current interpreter is not 3.11, it attempts to locate `python3.11`
specifically. If neither is available, it raises an error.

Output:
    Creates `venv/` directory structure with standard files (bin/activate, pyvenv.cfg, etc.).
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

from config import get_config, ensure_directories_exist
from utils.logger import get_logger, log_pipeline_start, log_pipeline_complete, log_pipeline_error

# Configure logger
logger = get_logger(__name__)

def check_python_version(version_str: str) -> bool:
    """Check if the given python version string is 3.11.x."""
    try:
        parts = version_str.split('.')
        major = int(parts[0])
        minor = int(parts[1])
        return major == 3 and minor == 11
    except (ValueError, IndexError):
        return False

def find_python311() -> str:
    """
    Attempt to find a python3.11 executable.
    Returns the path to the executable or raises FileNotFoundError.
    """
    # Common names for python 3.11
    candidates = ['python3.11', 'python3.11.exe']
    
    # First, try the current interpreter if it's 3.11
    if check_python_version(f"{sys.version_info.major}.{sys.version_info.minor}"):
        logger.info(f"Current interpreter is Python 3.11: {sys.executable}")
        return sys.executable

    # If not, search for python3.11 in PATH
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            version_output = result.stdout.strip()
            logger.info(f"Found candidate: {candidate} -> {version_output}")
            # Double check version string format (e.g., "Python 3.11.0")
            if '3.11' in version_output:
                return candidate
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    raise FileNotFoundError(
        "Could not find Python 3.11 executable. "
        "Please install Python 3.11 or ensure 'python3.11' is in your PATH. "
        f"Current interpreter: {sys.executable} ({sys.version})"
    )

def create_virtual_environment(venv_path: Path, python_exe: str) -> None:
    """
    Create a virtual environment at venv_path using the specified python executable.
    """
    if venv_path.exists():
        logger.warning(f"Virtual environment directory {venv_path} already exists. Removing it.")
        shutil.rmtree(venv_path)

    logger.info(f"Creating virtual environment at {venv_path} using {python_exe}...")
    
    try:
        subprocess.run(
            [python_exe, '-m', 'venv', str(venv_path)],
            check=True,
            capture_output=False # Stream output to see errors immediately
        )
        logger.info(f"Virtual environment created successfully at {venv_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create virtual environment: {e}")
        raise

def verify_venv(venv_path: Path) -> bool:
    """
    Verify that the virtual environment was created correctly and is a Python 3.11 env.
    """
    if not venv_path.exists():
        return False

    # Check for standard venv files
    bin_dir = venv_path / 'bin'
    if os.name == 'nt':
        bin_dir = venv_path / 'Scripts'
    
    activate_script = bin_dir / 'activate'
    if not activate_script.exists():
        logger.error(f"Activate script not found at {activate_script}")
        return False

    # Verify the python inside the venv is 3.11
    venv_python = bin_dir / 'python' if os.name != 'nt' else bin_dir / 'python.exe'
    if not venv_python.exists():
        logger.error(f"Python executable not found at {venv_python}")
        return False

    try:
        result = subprocess.run(
            [str(venv_python), '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        version_output = result.stdout.strip()
        if check_python_version(version_output.split()[-1]):
            logger.info(f"Verified venv Python version: {version_output}")
            return True
        else:
            logger.error(f"Venv Python version is not 3.11: {version_output}")
            return False
    except subprocess.CalledProcessError:
        logger.error("Could not determine venv Python version")
        return False

def run_setup_venv() -> None:
    """Main entry point for T002a."""
    config = get_config()
    project_root = config.get('project_root', Path.cwd())
    venv_dir = project_root / 'venv'

    log_pipeline_start("T002a", "Setup Python 3.11 Virtual Environment")

    try:
        # Ensure project root exists (should be done by T001a/b but safe to ensure)
        ensure_directories_exist([project_root])

        # Find Python 3.11
        python_exe = find_python311()

        # Create venv
        create_virtual_environment(venv_dir, python_exe)

        # Verify
        if verify_venv(venv_dir):
            log_pipeline_complete("T002a", f"Virtual environment created at {venv_dir}")
            print(f"SUCCESS: Virtual environment created at {venv_dir}")
        else:
            log_pipeline_error("T002a", "Verification of virtual environment failed.")
            raise RuntimeError("Virtual environment verification failed.")

    except Exception as e:
        log_pipeline_error("T002a", str(e))
        raise

def main():
    run_setup_venv()

if __name__ == "__main__":
    main()