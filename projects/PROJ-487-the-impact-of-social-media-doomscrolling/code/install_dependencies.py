"""
Script to install project dependencies from requirements.txt.
This script ensures all dependencies listed in code/requirements.txt are installed
in the current Python environment.
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

def install_dependencies():
    """
    Install dependencies from code/requirements.txt.
    
    Raises:
        SystemExit: If installation fails.
    """
    # Determine the project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    requirements_path = code_dir / "requirements.txt"

    if not requirements_path.exists():
        logger.error(f"Requirements file not found at: {requirements_path}")
        sys.exit(1)

    logger.info(f"Installing dependencies from: {requirements_path}")

    try:
        # Use pip from the current interpreter to ensure we install into the right env
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path), "--upgrade"],
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info("Installation output:")
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(line)
        
        if result.stderr:
            for line in result.stderr.splitlines():
                logger.warning(line)

        logger.info("Dependencies installed successfully.")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies. Exit code: {e.returncode}")
        if e.stdout:
            logger.error(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during installation: {e}")
        sys.exit(1)

def main():
    """Entry point for the script."""
    install_dependencies()

if __name__ == "__main__":
    main()