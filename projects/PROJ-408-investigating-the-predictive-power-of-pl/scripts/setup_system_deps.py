#!/usr/bin/env python3
"""
Setup script to install and verify system dependencies (mafft, fasttree).

This script attempts to install the required system binaries using the
system package manager (apt-get for Debian/Ubuntu-based runners) and
verifies their presence in the PATH.

Constraints:
- Must verify binaries are in PATH before proceeding.
- Must fail loudly if installation or verification fails.
"""
import subprocess
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_BINARIES = {
    'mafft': 'mafft',
    'fasttree': 'FastTree'
}

def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout.strip())
        if result.stderr:
            logger.info(result.stderr.strip())
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr.strip()}")
        raise

def check_binary_exists(binary_name: str) -> bool:
    """Check if a binary exists in the system PATH."""
    path = shutil.which(binary_name)
    return path is not None

def install_dependencies() -> None:
    """Install system dependencies using apt-get."""
    logger.info("Updating package lists...")
    run_command(['sudo', 'apt-get', 'update'])

    logger.info("Installing mafft and fasttree...")
    # Install mafft and fasttree
    run_command(['sudo', 'apt-get', 'install', '-y', 'mafft', 'fasttree'])

def verify_installation() -> bool:
    """Verify that all required binaries are installed and in PATH."""
    all_present = True
    for binary_name, expected_cmd in REQUIRED_BINARIES.items():
        if check_binary_exists(binary_name):
            logger.info(f"✓ {binary_name} is installed and in PATH")
            # Verify version or basic functionality
            try:
                run_command([binary_name, '--version'], check=False)
            except Exception as e:
                logger.warning(f"Could not verify version for {binary_name}: {e}")
        else:
            logger.error(f"✗ {binary_name} is NOT found in PATH")
            all_present = False
    
    return all_present

def main():
    """Main entry point for the setup script."""
    logger.info("Starting system dependency setup for PROJ-408...")
    
    # Check if we are on a system that uses apt-get
    # This is a heuristic; in a real CI/CD environment, the OS is usually known.
    if not os.path.exists('/etc/apt'):
        logger.warning("This script is designed for Debian/Ubuntu-based systems.")
        logger.warning("Attempting to verify binaries without installation...")
        if verify_installation():
            logger.info("All binaries are already present.")
            return 0
        else:
            logger.error("Binaries missing and cannot auto-install on this OS.")
            return 1

    # Attempt installation
    try:
        install_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during installation: {e}")
        return 1

    # Verify installation
    if verify_installation():
        logger.info("System dependency setup completed successfully.")
        return 0
    else:
        logger.error("System dependency setup failed: binaries not found.")
        return 1

if __name__ == "__main__":
    # Import shutil here to avoid global scope issues if not needed
    import shutil
    sys.exit(main())
