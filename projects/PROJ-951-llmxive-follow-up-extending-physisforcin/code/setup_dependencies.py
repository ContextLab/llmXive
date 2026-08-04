import subprocess
import sys
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Ensure Python version is 3.9 or higher."""
    if sys.version_info < (3, 9):
        logger.error(f"Python 3.9+ required. Current version: {sys.version}")
        sys.exit(1)
    logger.info(f"Python version check passed: {sys.version}")

def install_packages(requirements_path: Path):
    """Install packages from requirements.txt, forcing CPU-only torch."""
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        sys.exit(1)

    logger.info(f"Installing packages from {requirements_path}...")
    
    # Explicitly install torch CPU first to avoid GPU conflicts
    logger.info("Installing CPU-only PyTorch explicitly...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "torch==2.3.0", 
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ])
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install CPU PyTorch: {e}")
        sys.exit(1)

    # Install remaining packages
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ])
        logger.info("All packages installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install requirements: {e}")
        sys.exit(1)

def verify_cpu_only():
    """Verify that CUDA is not available in PyTorch."""
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available! This project is designed for CPU-only execution.")
            logger.warning("To force CPU mode, set environment variable: export CUDA_VISIBLE_DEVICES=''")
        else:
            logger.info("Verified: PyTorch is running in CPU-only mode.")
    except ImportError:
        logger.error("PyTorch not found. Installation failed.")
        sys.exit(1)

def verify_imports():
    """Verify that all critical packages can be imported."""
    packages = [
        'torch', 'pybullet', 'mujoco', 'diffusers', 
        'transformers', 'sklearn', 'cv2', 'pandas', 
        'numpy', 'requests', 'datasets'
    ]
    
    failed = []
    for pkg in packages:
        try:
            __import__(pkg)
            logger.debug(f"Successfully imported: {pkg}")
        except ImportError as e:
            logger.error(f"Failed to import {pkg}: {e}")
            failed.append(pkg)
    
    if failed:
        logger.error(f"Missing packages: {failed}")
        sys.exit(1)
    
    logger.info("All required packages verified.")

def main():
    """Main entry point for dependency setup."""
    check_python_version()
    
    # Determine project root (assume code/ is current dir or parent)
    if Path.cwd().name == 'code':
        root = Path.cwd().parent
    else:
        root = Path.cwd()
    
    req_file = root / 'code' / 'requirements.txt'
    
    if not req_file.exists():
        logger.error(f"Requirements file missing at {req_file}")
        sys.exit(1)
    
    install_packages(req_file)
    verify_cpu_only()
    verify_imports()
    logger.info("Project dependency initialization complete.")

if __name__ == "__main__":
    main()
