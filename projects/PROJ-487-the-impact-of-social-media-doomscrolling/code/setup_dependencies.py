"""
Dependency installation script for PROJ-487.
Reads requirements.txt and installs packages using pip.
"""
import os
import sys
import subprocess
from pathlib import Path
import logging

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def install_dependencies(requirements_path: Path) -> bool:
    """
    Install dependencies from a requirements.txt file.

    Args:
        requirements_path: Path to requirements.txt

    Returns:
        True if installation succeeded, False otherwise.
    """
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        return False

    logger.info(f"Installing dependencies from {requirements_path}...")
    
    try:
        # Use pip from the current environment
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            cwd=project_root
        )
        logger.info("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during installation: {e}")
        return False

def main():
    """Main entry point for dependency installation."""
    # Determine requirements path relative to project root
    requirements_path = project_root / "requirements.txt"
    
    if not requirements_path.exists():
        logger.error("requirements.txt not found in project root.")
        sys.exit(1)

    success = install_dependencies(requirements_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
