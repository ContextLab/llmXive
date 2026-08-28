import os
import sys
import venv
import subprocess
from pathlib import Path
import logging

from utils.logging import get_logger

def setup_venv(project_root: Path) -> bool:
    """
    Create a Python virtual environment in the project root.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        True if successful, False otherwise
    """
    logger = get_logger(__name__)
    venv_path = project_root / "venv"
    
    if venv_path.exists():
        logger.info(f"Virtual environment already exists at {venv_path}")
        return True
    
    try:
        logger.info(f"Creating virtual environment at {venv_path}...")
        venv.create(venv_path, with_pip=True)
        
        # Verify the venv was created successfully
        if not (venv_path / "bin" / "activate").exists():
            # Check for Windows
            if not (venv_path / "Scripts" / "activate.bat").exists():
                logger.error("Virtual environment creation failed: activation script not found")
                return False
        
        logger.info("Virtual environment created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False

def main():
    """Main entry point for setup_venv script."""
    # Determine project root (parent of code directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    logger = get_logger(__name__)
    logger.info(f"Project root: {project_root}")
    
    success = setup_venv(project_root)
    
    if success:
        logger.info("Setup complete")
        sys.exit(0)
    else:
        logger.error("Setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
