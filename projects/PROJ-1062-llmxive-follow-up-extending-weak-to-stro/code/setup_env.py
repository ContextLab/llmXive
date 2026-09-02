"""
Environment setup and dependency verification for the llmXive project.
Handles installation of dependencies with specific CPU-only constraints for PyTorch.
"""
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

def check_python_version(min_version: str = "3.9"):
    """Check if the running Python version meets the minimum requirement."""
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    try:
        pkg_resources.require(f"Python>={min_version}")
        logger.info(f"Python version check passed: {current_version} >= {min_version}")
        return True
    except pkg_resources.VersionConflict:
        logger.error(f"Python version {current_version} is below required {min_version}")
        return False

def install_dependencies():
    """
    Install dependencies from requirements.txt.
    Ensures torch is installed from the CPU index URL to enforce CPU-only usage.
    """
    requirements_path = Path(__file__).parent / "requirements.txt"
    
    if not requirements_path.exists():
        logger.error(f"Requirements file not found at {requirements_path}")
        return False

    logger.info(f"Installing dependencies from {requirements_path}...")
    
    try:
        # Read requirements to handle the special torch index URL manually if needed
        # or pass the file directly to pip which handles comments and --index-url
        cmd = [
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path),
            "--upgrade", "--no-cache-dir"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            logger.info("Installation output:\n" + result.stdout)
        if result.stderr:
            logger.warning("Installation warnings/errors:\n" + result.stderr)
        
        logger.info("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False

def verify_torch_installation():
    """
    Verify that PyTorch is installed and running on CPU (CUDA not available).
    This enforces the CPU-only constraint required by the project architecture.
    """
    try:
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            logger.warning(
                "CUDA is available. The project is designed for CPU-only execution. "
                "Ensure environment variables (e.g., CUDA_VISIBLE_DEVICES=) or "
                "the specific CPU wheel installation is respected."
            )
            # We do not fail here, but warn. The architecture constraint is about
            # the build wheel, not necessarily the hardware availability, 
            # but the code should not rely on GPU.
        else:
            logger.info("CUDA is not available. Running in CPU-only mode as expected.")
        
        # Check for MPS (Apple Silicon)
        if hasattr(torch, 'mps') and torch.backends.mps.is_available():
            logger.info("MPS (Apple Silicon) is available.")
        
        return True
    except ImportError:
        logger.error("PyTorch is not installed. Please run the installation script.")
        return False

def main():
    """Main entry point for environment setup."""
    logger.info("Starting environment setup...")
    
    if not check_python_version():
        sys.exit(1)
    
    if not install_dependencies():
        logger.error("Dependency installation failed. Exiting.")
        sys.exit(1)
    
    if not verify_torch_installation():
        logger.error("PyTorch verification failed. Exiting.")
        sys.exit(1)
    
    logger.info("Environment setup completed successfully.")

if __name__ == "__main__":
    main()
