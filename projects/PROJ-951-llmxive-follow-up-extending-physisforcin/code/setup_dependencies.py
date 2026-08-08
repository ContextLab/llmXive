import subprocess
import sys
import logging
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        logger.error(f"Python 3.9+ is required. Current version: {sys.version}")
        sys.exit(1)
    logger.info(f"Python version check passed: {sys.version}")

def install_packages():
    """Install dependencies from requirements.txt."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    if not requirements_path.exists():
        logger.error("requirements.txt not found.")
        sys.exit(1)

    logger.info(f"Installing packages from {requirements_path}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path), "--upgrade"
        ])
        logger.info("Package installation successful.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Package installation failed: {e}")
        sys.exit(1)

def verify_cpu_only():
    """Verify that critical libraries are running on CPU."""
    logger.info("Verifying CPU-only execution...")
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available. Ensure CUDA_VISIBLE_DEVICES is unset for CPU-only mode.")
        
        import pybullet
        import mujoco
        logger.info("CPU-only verification passed.")
    except ImportError as e:
        logger.error(f"Import error during verification: {e}")
        sys.exit(1)

def verify_imports():
    """Verify all required packages can be imported."""
    packages = [
        'torch', 'pybullet', 'mujoco', 'diffusers', 'transformers',
        'scikit-learn', 'cv2', 'pandas', 'numpy', 'requests', 'datasets'
    ]
    failed = []
    for pkg in packages:
        try:
            if pkg == 'cv2':
                import cv2
            else:
                __import__(pkg)
            logger.info(f"Successfully imported {pkg}.")
        except ImportError:
            failed.append(pkg)
            logger.error(f"Failed to import {pkg}.")
    
    if failed:
        logger.error(f"Missing packages: {failed}")
        sys.exit(1)
    logger.info("All imports verified.")

def main():
    check_python_version()
    install_packages()
    verify_imports()
    verify_cpu_only()
    logger.info("Setup dependencies completed successfully.")

if __name__ == "__main__":
    main()