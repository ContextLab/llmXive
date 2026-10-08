"""
Environment Setup Script for PROJ-191.

This script initializes the Python virtual environment and installs
pinned dependencies from requirements.txt.
"""
import os
import subprocess
import sys
from pathlib import Path
import logging

from config import get_logger, setup_logging

def main():
    """
    Main entry point for environment setup.
    
    1. Creates a virtual environment in 'venv'.
    2. Activates it.
    3. Installs dependencies from 'requirements.txt'.
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Determine paths relative to this script's location (code/)
    project_root = Path(__file__).parent.parent
    code_dir = Path(__file__).parent
    venv_path = code_dir / "venv"
    requirements_path = code_dir / "requirements.txt"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Code directory: {code_dir}")
    logger.info(f"Venv path: {venv_path}")
    logger.info(f"Requirements path: {requirements_path}")
    
    if not requirements_path.exists():
        logger.error(f"Requirements file not found at {requirements_path}")
        sys.exit(1)
    
    # Step 1: Create virtual environment
    logger.info("Creating virtual environment...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create virtual environment: {e.stderr.decode()}")
        sys.exit(1)
    
    # Step 2: Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/Mac
        pip_path = venv_path / "bin" / "pip"
        
    if not pip_path.exists():
        logger.error(f"Pip executable not found at {pip_path}")
        sys.exit(1)
    
    # Step 3: Upgrade pip first (optional but good practice)
    logger.info("Upgrading pip...")
    try:
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Pip upgraded successfully.")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to upgrade pip (continuing anyway): {e.stderr.decode()}")
    
    # Step 4: Install dependencies
    logger.info("Installing dependencies from requirements.txt...")
    try:
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e.stderr.decode()}")
        sys.exit(1)
    
    logger.info("Environment setup complete.")
    
if __name__ == "__main__":
    main()