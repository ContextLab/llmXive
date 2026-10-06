"""
Environment setup script for PROJ-191.
Initializes the Python project environment by installing pinned dependencies.
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
    1. Verifies the requirements.txt exists in the code directory.
    2. Installs dependencies using pip.
    """
    # Initialize logging
    log = get_logger(__name__)
    
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    requirements_path = code_dir / "requirements.txt"

    if not requirements_path.exists():
        log.error(f"requirements.txt not found at {requirements_path}")
        sys.exit(1)

    log.info(f"Found requirements.txt at {requirements_path}")
    log.info("Installing dependencies...")

    try:
        # Run pip install in the current environment
        # Use sys.executable to ensure we install into the correct python env
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            cwd=code_dir
        )
        log.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to install dependencies: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_logging()
    main()