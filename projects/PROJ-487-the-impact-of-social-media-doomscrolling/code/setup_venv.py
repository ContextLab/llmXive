"""
Setup Python virtual environment for the project.

This script creates a virtual environment in the project root directory.
It ensures that the 'venv' directory exists and contains the necessary
activation scripts and dependencies.
"""
import os
import sys
import venv
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_venv(project_root: Path) -> bool:
    """
    Create a Python virtual environment in the project root.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        True if successful, False otherwise
    """
    venv_path = project_root / "venv"
    
    if venv_path.exists():
        logger.info(f"Virtual environment already exists at {venv_path}")
        # Verify it's a valid venv
        if not (venv_path / "bin" / "activate").exists() and \
           not (venv_path / "Scripts" / "activate").exists():
            logger.warning("Existing venv appears corrupted, recreating...")
            import shutil
            shutil.rmtree(venv_path)
        else:
            return True
    
    logger.info(f"Creating virtual environment at {venv_path}")
    try:
        venv.create(venv_path, with_pip=True)
        logger.info("Virtual environment created successfully")
        
        # Upgrade pip to ensure latest version
        pip_path = venv_path / "bin" / "pip" if os.name != 'nt' else venv_path / "Scripts" / "pip"
        if pip_path.exists():
            logger.info("Upgrading pip...")
            subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        return True
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False

def main():
    """Main entry point for the script."""
    # Determine project root
    # The script is located at code/setup_venv.py, so project root is parent of parent
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # Goes up from code/ to project root
    
    logger.info(f"Project root: {project_root}")
    
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)
    
    success = setup_venv(project_root)
    
    if success:
        logger.info("Virtual environment setup completed successfully")
        sys.exit(0)
    else:
        logger.error("Virtual environment setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
