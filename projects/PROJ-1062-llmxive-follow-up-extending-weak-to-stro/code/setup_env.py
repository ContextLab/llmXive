import sys
import subprocess
import logging
from pathlib import Path
import pkg_resources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version(min_version=(3, 9)):
    """Check if the current Python version meets the minimum requirement."""
    current = sys.version_info[:2]
    if current < min_version:
        error_msg = f"Python version {min_version[0]}.{min_version[1]}+ is required. Found: {sys.version}"
        logger.error(error_msg)
        raise SystemExit(error_msg)
    logger.info(f"Python version check passed: {sys.version}")
    return True

def install_dependencies():
    """Install dependencies from requirements.txt."""
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        error_msg = "requirements.txt not found in the project root."
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    logger.info(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path), "--quiet"])
        logger.info("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to install dependencies: {e}"
        logger.error(error_msg)
        raise SystemExit(error_msg)

def verify_torch_installation():
    """Verify that torch is installed and CPU-only (no CUDA available)."""
    try:
        import torch
        logger.info(f"Torch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            logger.warning("CUDA is available. Note: This project targets CPU-only execution (FR-007).")
            # We do not fail here if CUDA is available, but we log a warning.
            # The constraint is about running on CPU, not banning CUDA hardware.
            # However, if the requirement is strictly CPU-only inference, we might want to ensure we don't accidentally use GPU.
        else:
            logger.info("CUDA is not available (CPU-only mode confirmed).")
        
        # Check for bitsandbytes version if installed
        try:
            import bitsandbytes
            logger.info(f"bitsandbytes version: {bitsandbytes.__version__}")
            if bitsandbytes.__version__ != "0.43.0":
                logger.warning(f"bitsandbytes version mismatch. Expected 0.43.0, found {bitsandbytes.__version__}")
        except ImportError:
            logger.warning("bitsandbytes is not installed. Some features may be unavailable.")
        
        return True
    except ImportError as e:
        error_msg = f"Torch is not installed or import failed: {e}"
        logger.error(error_msg)
        raise SystemExit(error_msg)

def main():
    """Main entry point for environment setup."""
    logger.info("Starting environment setup...")
    
    try:
        check_python_version()
        install_dependencies()
        verify_torch_installation()
        logger.info("Environment setup completed successfully.")
    except SystemExit as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
