"""
Script to install project dependencies from requirements.txt.

This script executes the installation command and verifies the
successful installation of core dependencies (specifically torch).
"""
import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install dependencies from requirements.txt using the CPU index URL."""
    requirements_path = Path("code/requirements.txt")
    
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        sys.exit(1)
    
    logger.info(f"Installing dependencies from {requirements_path}...")
    
    # Use the CPU-specific PyTorch index URL as specified in the task
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements_path),
        "--index-url",
        "https://download.pytorch.org/whl/cpu"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        logger.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies. Exit code: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("pip not found. Please ensure pip is installed and in PATH.")
        sys.exit(1)

def verify_installation():
    """Verify that torch is installed and print its version."""
    logger.info("Verifying torch installation...")
    try:
        import torch
        version = torch.__version__
        logger.info(f"PyTorch version: {version}")
        
        # Additional verification: check if basic CUDA/CPU availability works
        # Note: We are using CPU-only build, so CUDA availability is not expected
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"PyTorch is running on: {device}")
        
        return True
    except ImportError as e:
        logger.error(f"PyTorch import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False

def main():
    """Main entry point for the script."""
    logger.info("Starting dependency installation and verification...")
    
    install_dependencies()
    
    if verify_installation():
        logger.info("All checks passed. Dependencies are ready.")
        sys.exit(0)
    else:
        logger.error("Verification failed. Installation may be incomplete.")
        sys.exit(1)

if __name__ == "__main__":
    main()