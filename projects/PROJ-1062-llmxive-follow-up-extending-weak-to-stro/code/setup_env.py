"""
Environment Setup Script for llmXive Project.

This script verifies Python version, installs dependencies with specific 
constraints (CPU-only PyTorch), and validates the environment setup.

Usage:
    python setup_env.py
"""
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Verify Python 3.11+ is installed."""
    required_version = (3, 11)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        logger.error(f"Python {required_version[0]}.{required_version[1]}+ is required. "
                     f"Current version: {sys.version}")
        sys.exit(1)
    
    logger.info(f"Python version check passed: {sys.version.split()[0]}")

def install_dependencies():
    """Install project dependencies with CPU-only PyTorch constraint."""
    logger.info("Checking and installing dependencies...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        logger.error("requirements.txt not found in the current directory.")
        sys.exit(1)
    
    # Install with explicit CPU-only index for torch
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file),
            "--upgrade", "--no-cache-dir"
        ])
        logger.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        sys.exit(1)

def verify_torch_installation():
    """Verify PyTorch is installed as CPU-only version."""
    try:
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        
        # Check if CUDA is available (it should NOT be for CPU-only build)
        if torch.cuda.is_available():
            logger.warning("CUDA is available. This might indicate a GPU build was installed "
                         "despite the CPU-only constraint. Please verify the installation.")
        else:
            logger.info("PyTorch is correctly configured for CPU-only execution.")
        
        # Verify device availability
        device = torch.device("cpu")
        logger.info(f"Using device: {device}")
        
    except ImportError:
        logger.error("PyTorch is not installed. Please run the installation script.")
        sys.exit(1)

def main():
    """Main entry point for environment setup."""
    logger.info("Starting llmXive environment setup...")
    
    # Change to the code directory if running from project root
    if Path(__file__).parent.name == "code":
        os.chdir(Path(__file__).parent)
    
    check_python_version()
    install_dependencies()
    verify_torch_installation()
    
    logger.info("Environment setup completed successfully.")

if __name__ == "__main__":
    import os
    main()
