import os
import sys
import venv
import subprocess
from pathlib import Path
import logging

from utils.logging import get_logger

def setup_venv(venv_path: Path) -> bool:
    """
    Initialize a Python virtual environment at the specified path.
    
    Args:
        venv_path: Path where the virtual environment should be created.
        
    Returns:
        True if successful, False otherwise.
    """
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Creating virtual environment at {venv_path}")
        
        # Create the virtual environment
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_path)
        
        logger.info("Virtual environment created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False

def main():
    """Main entry point for setting up the virtual environment."""
    # Configure logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Determine project root (assuming script is in code/ directory)
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"
    
    # Check if venv already exists
    if venv_path.exists():
        logger.warning(f"Virtual environment already exists at {venv_path}")
        # Verify it has the activate script
        activate_script = venv_path / "bin" / "activate"
        if activate_script.exists():
            logger.info("Verification: venv/bin/activate exists")
            return 0
        else:
            logger.error("Verification failed: venv/bin/activate does not exist")
            return 1
    
    # Create the virtual environment
    success = setup_venv(venv_path)
    
    if not success:
        logger.error("Failed to create virtual environment")
        return 1
    
    # Verify the activate script exists
    activate_script = venv_path / "bin" / "activate"
    if not activate_script.exists():
        logger.error("Verification failed: venv/bin/activate does not exist after creation")
        return 1
    
    logger.info("Verification successful: venv/bin/activate exists")
    return 0

if __name__ == "__main__":
    sys.exit(main())
