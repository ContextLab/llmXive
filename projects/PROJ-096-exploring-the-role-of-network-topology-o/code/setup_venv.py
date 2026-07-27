"""
Script to initialize a Python virtual environment and install dependencies.

This script corresponds to task T002b: Initialize Virtual Environment.
It creates a virtual environment in `code/.venv` and installs dependencies
from `code/requirements.txt`.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

def init_logging():
    """Initialize logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point for virtual environment setup."""
    init_logging()
    logger = logging.getLogger(__name__)

    # Define paths
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    venv_path = code_dir / ".venv"
    requirements_path = code_dir / "requirements.txt"

    # Check if requirements.txt exists
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        sys.exit(1)

    # Check if virtual environment already exists
    if venv_path.exists():
        logger.info(f"Virtual environment already exists at {venv_path}")
        logger.info("Skipping creation, proceeding to install dependencies...")
    else:
        logger.info(f"Creating virtual environment at {venv_path}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e.stderr}")
            sys.exit(1)

    # Determine pip executable path
    if os.name == 'nt':
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"

    # Upgrade pip first
    logger.info("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Pip upgraded successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upgrade pip: {e.stderr}")
        sys.exit(1)

    # Install dependencies
    logger.info(f"Installing dependencies from {requirements_path}...")
    try:
        result = subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_path)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Dependencies installed successfully.")
        if result.stdout:
            logger.debug(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e.stderr}")
        sys.exit(1)

    # Verify installation of a key package (networkx)
    logger.info("Verifying installation of key packages...")
    try:
        result = subprocess.run(
            [str(pip_path), "list"],
            check=True,
            capture_output=True,
            text=True
        )
        if "networkx" in result.stdout.lower():
            logger.info("networkx is installed.")
        else:
            logger.warning("networkx not found in installed packages.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to verify installed packages: {e.stderr}")
        sys.exit(1)

    logger.info("Virtual environment setup completed successfully.")

if __name__ == "__main__":
    main()