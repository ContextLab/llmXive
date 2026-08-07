"""
T002 Implementation: Initialize Python project dependencies.
Installs CPU-only versions of required packages and verifies imports.
"""
import subprocess
import sys
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/setup_dependencies.log')
    ]
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Verify Python version is >= 3.9"""
    if sys.version_info < (3, 9):
        logger.error(f"Python 3.9+ required. Found {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    logger.info(f"Python version verified: {sys.version}")

def install_packages():
    """Install dependencies from requirements.txt"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        logger.error("requirements.txt not found. Please create it first.")
        sys.exit(1)

    logger.info(f"Installing dependencies from {req_file.absolute()}...")
    try:
        # Install with --no-cache-dir to avoid disk bloat and force fresh fetch
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", str(req_file),
            "--no-cache-dir",
            "-q"
        ])
        logger.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        sys.exit(1)

def verify_cpu_only():
    """Verify that CPU-only versions of torch are installed and CUDA is not available"""
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available. Ensure CPU-only usage is enforced in code.")
        else:
            logger.info("PyTorch CPU-only mode confirmed (no CUDA detected).")
        
        # Check for specific CPU flags if possible
        if hasattr(torch.version, 'cuda') and torch.version.cuda is None:
            logger.info("PyTorch built without CUDA support (CPU-only).")
    except ImportError:
        logger.error("PyTorch not found. Installation failed.")
        sys.exit(1)

    # Verify other critical packages
    packages = ['pybullet', 'mujoco', 'diffusers', 'transformers', 'sklearn', 'cv2', 'pandas', 'numpy', 'requests', 'datasets']
    for pkg in packages:
        try:
            __import__(pkg)
            logger.info(f"Package '{pkg}' verified.")
        except ImportError:
            logger.error(f"Package '{pkg}' not found.")
            sys.exit(1)

def verify_imports():
    """Detailed import verification for all task requirements"""
    logger.info("Verifying imports...")
    errors = []
    
    # Torch CPU check
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA detected, but proceeding with CPU enforcement in scripts.")
    except Exception as e:
        errors.append(f"torch: {e}")

    # PyBullet
    try:
        import pybullet as p
        logger.info("PyBullet imported successfully.")
    except Exception as e:
        errors.append(f"pybullet: {e}")

    # MuJoCo
    try:
        import mujoco
        logger.info("MuJoCo imported successfully.")
    except Exception as e:
        errors.append(f"mujoco: {e}")

    # Diffusers
    try:
        import diffusers
        logger.info("Diffusers imported successfully.")
    except Exception as e:
        errors.append(f"diffusers: {e}")

    # Transformers
    try:
        import transformers
        logger.info("Transformers imported successfully.")
    except Exception as e:
        errors.append(f"transformers: {e}")

    # Scikit-learn
    try:
        import sklearn
        logger.info("Scikit-learn imported successfully.")
    except Exception as e:
        errors.append(f"scikit-learn: {e}")

    # OpenCV
    try:
        import cv2
        logger.info("OpenCV imported successfully.")
    except Exception as e:
        errors.append(f"opencv-python: {e}")

    # Pandas
    try:
        import pandas as pd
        logger.info("Pandas imported successfully.")
    except Exception as e:
        errors.append(f"pandas: {e}")

    # NumPy
    try:
        import numpy as np
        logger.info("NumPy imported successfully.")
    except Exception as e:
        errors.append(f"numpy: {e}")

    # Requests
    try:
        import requests
        logger.info("Requests imported successfully.")
    except Exception as e:
        errors.append(f"requests: {e}")

    # Datasets
    try:
        import datasets
        logger.info("Datasets imported successfully.")
    except Exception as e:
        errors.append(f"datasets: {e}")

    if errors:
        logger.error(f"Import verification failed: {errors}")
        sys.exit(1)
    
    logger.info("All imports verified successfully.")

def main():
    """Main entry point for T002"""
    logger.info("Starting T002: Initialize Python project dependencies...")
    check_python_version()
    install_packages()
    verify_cpu_only()
    verify_imports()
    logger.info("T002 completed successfully.")

if __name__ == "__main__":
    main()
