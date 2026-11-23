"""
Task T002b: Setup Python 3.11 virtual environment and install dependencies.

This script creates a virtual environment in code/.venv using the system's
Python 3.11 interpreter, installs dependencies from requirements.txt, and
verifies the installation.

Verification:
Run: code/.venv/bin/python --version
Assert: Output contains '3.11'
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is the parent of the code/ directory
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
VENV_DIR = CODE_DIR / ".venv"
REQUIREMENTS_FILE = CODE_DIR / "requirements.txt"

def check_python_version() -> bool:
    """Check if Python 3.11 is available in the system PATH."""
    logger.info("Checking for Python 3.11 availability...")
    
    # Try common python3.11 executable names
    python_executables = ['python3.11', 'python3.11.exe']
    found = False
    python_path = None
    
    for exe in python_executables:
        try:
            result = subprocess.run(
                [exe, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version_output = result.stderr.strip() if result.stderr else result.stdout.strip()
                if '3.11' in version_output:
                    logger.info(f"Found Python 3.11: {exe} -> {version_output}")
                    found = True
                    python_path = exe
                    break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    if not found:
        # Fallback: check if current python is 3.11
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if current_version.startswith("3.11"):
            logger.info(f"Current Python is 3.11: {sys.executable}")
            found = True
            python_path = sys.executable
        else:
            logger.error(f"Python 3.11 not found. Current version: {current_version}")
            logger.error("Please install Python 3.11 and ensure it is in PATH as 'python3.11'")
            return False
    
    return True

def create_virtual_environment() -> bool:
    """Create a virtual environment in code/.venv."""
    logger.info(f"Creating virtual environment at {VENV_DIR}...")
    
    # Remove existing venv if it exists
    if VENV_DIR.exists():
        logger.warning(f"Removing existing virtual environment at {VENV_DIR}")
        shutil.rmtree(VENV_DIR)
    
    # Create new venv
    try:
        # Use the found python3.11 if available, otherwise use current python
        python_exec = sys.executable
        result = subprocess.run(
            [python_exec, "-m", "venv", str(VENV_DIR)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to create virtual environment: {result.stderr}")
            return False
        
        logger.info("Virtual environment created successfully")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Timeout while creating virtual environment")
        return False
    except Exception as e:
        logger.error(f"Error creating virtual environment: {e}")
        return False

def install_dependencies() -> bool:
    """Install dependencies from requirements.txt into the virtual environment."""
    logger.info("Installing dependencies from requirements.txt...")
    
    if not REQUIREMENTS_FILE.exists():
        logger.error(f"Requirements file not found: {REQUIREMENTS_FILE}")
        return False
    
    # Determine the pip executable path
    if os.name == 'nt':  # Windows
        pip_exec = VENV_DIR / "Scripts" / "pip.exe"
    else:  # Unix/Linux/Mac
        pip_exec = VENV_DIR / "bin" / "pip"
    
    if not pip_exec.exists():
        logger.error(f"Pip executable not found at {pip_exec}")
        return False
    
    try:
        # Upgrade pip first
        logger.info("Upgrading pip...")
        result = subprocess.run(
            [str(pip_exec), "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            logger.warning(f"Warning: pip upgrade failed: {result.stderr}")
            # Continue anyway, might still work
        
        # Install requirements
        logger.info(f"Installing requirements from {REQUIREMENTS_FILE}...")
        result = subprocess.run(
            [str(pip_exec), "install", "-r", str(REQUIREMENTS_FILE)],
            capture_output=True,
            text=True,
            timeout=600  # Longer timeout for dependency installation
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to install dependencies: {result.stderr}")
            logger.error(f"stdout: {result.stdout}")
            return False
        
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Timeout while installing dependencies")
        return False
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        return False

def verify_installation() -> bool:
    """Verify that the virtual environment is using Python 3.11."""
    logger.info("Verifying Python version in virtual environment...")
    
    # Determine the python executable path
    if os.name == 'nt':  # Windows
        python_exec = VENV_DIR / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        python_exec = VENV_DIR / "bin" / "python"
    
    if not python_exec.exists():
        logger.error(f"Python executable not found at {python_exec}")
        return False
    
    try:
        result = subprocess.run(
            [str(python_exec), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        version_output = result.stderr.strip() if result.stderr else result.stdout.strip()
        logger.info(f"Virtual environment Python version: {version_output}")
        
        if '3.11' in version_output:
            logger.info("Verification successful: Virtual environment uses Python 3.11")
            return True
        else:
            logger.error(f"Verification failed: Expected Python 3.11, got {version_output}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout while verifying Python version")
        return False
    except Exception as e:
        logger.error(f"Error verifying Python version: {e}")
        return False

def main():
    """Main entry point for the virtual environment setup."""
    logger.info("=" * 60)
    logger.info("Starting Python 3.11 Virtual Environment Setup (Task T002b)")
    logger.info("=" * 60)
    
    # Check for Python 3.11
    if not check_python_version():
        logger.error("Aborting: Python 3.11 not available")
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        logger.error("Aborting: Failed to create virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        logger.error("Aborting: Failed to install dependencies")
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        logger.error("Aborting: Verification failed")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Virtual environment setup completed successfully!")
    logger.info(f"Activate with: source {VENV_DIR}/bin/activate  (Unix/Mac)")
    logger.info(f"Activate with: {VENV_DIR}\\Scripts\\activate  (Windows)")
    logger.info("=" * 60)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
