"""
Environment setup script for llmXive project.
Verifies Python version, installs dependencies, and ensures CPU-only execution.
"""
import sys
import subprocess
import importlib
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version(min_version=(3, 10)):
    """Check if current Python version meets minimum requirements."""
    current = sys.version_info[:2]
    if current < min_version:
        raise RuntimeError(
            f"Python {min_version[0]}.{min_version[1]}+ is required. "
            f"Found {sys.version_info.major}.{sys.version_info.minor}."
        )
    logger.info(f"Python version check passed: {sys.version}")

def check_package_installed(package_name):
    """Check if a package is installed."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_packages(requirements_path):
    """Install packages from a requirements.txt file."""
    if not requirements_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")

    logger.info(f"Installing packages from {requirements_path}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path),
            "--upgrade", "--no-cache-dir"
        ])
        logger.info("Package installation successful.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {e}")
        raise

def verify_cpu_only():
    """
    Verify that CUDA is not being used by PyTorch or other libraries.
    This is a soft check; environment variables or hardware might still force GPU.
    """
    logger.info("Verifying CPU-only configuration...")
    
    # Check PyTorch
    if check_package_installed('torch'):
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available. Forcing CPU usage via environment variable.")
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            # Re-import to ensure it picks up the change (might not work in all cases)
            import importlib
            importlib.reload(torch)
            if torch.cuda.is_available():
                logger.error("Failed to disable CUDA. Please run with CUDA_VISIBLE_DEVICES=''")
                raise RuntimeError("CUDA detected and could not be disabled.")
        else:
            logger.info("PyTorch CPU-only mode confirmed.")
    
    # Check other potential GPU libraries
    if check_package_installed('mujoco'):
        # MuJoCo usually defaults to CPU unless GL rendering is forced
        logger.info("MuJoCo check: Ensure headless rendering is used.")

def verify_imports():
    """Verify that all critical packages can be imported."""
    critical_packages = [
        'torch', 'diffusers', 'transformers', 'pybullet', 'mujoco',
        'pandas', 'numpy', 'requests', 'datasets', 'sklearn', 'cv2'
    ]
    
    missing = []
    for pkg in critical_packages:
        # Handle sklearn vs scikit-learn
        import_name = 'sklearn' if pkg == 'sklearn' else pkg
        if not check_package_installed(import_name):
            missing.append(pkg)
    
    if missing:
        raise ImportError(f"Missing critical packages: {missing}")
    
    logger.info("All critical packages imported successfully.")

def main():
    """Main entry point for environment setup."""
    logger.info("Starting environment setup...")
    
    # 1. Check Python version
    check_python_version()
    
    # 2. Locate requirements file
    # Assume script is in code/ and requirements.txt is in code/
    script_dir = Path(__file__).parent.resolve()
    requirements_path = script_dir / "requirements.txt"
    
    # 3. Install packages
    if not requirements_path.exists():
        logger.warning(f"Requirements file not found at {requirements_path}. Skipping installation.")
        logger.warning("Please ensure requirements.txt exists and run 'pip install -r requirements.txt' manually.")
    else:
        install_packages(requirements_path)
    
    # 4. Verify CPU-only
    verify_cpu_only()
    
    # 5. Verify imports
    verify_imports()
    
    logger.info("Environment setup complete.")

if __name__ == "__main__":
    main()
