"""
Environment setup script for llmXive Physics Filter project.
Verifies Python 3.11+ and installs/validates CPU-only dependencies.
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
logger = logging.getLogger("setup_env")

REQUIRED_PYTHON_VERSION = (3, 11)

def check_python_version():
    """Verify Python version is >= 3.11."""
    if sys.version_info < REQUIRED_PYTHON_VERSION:
        logger.error(f"Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}+ is required. "
                     f"Current version: {sys.version}")
        return False
    logger.info(f"Python version check passed: {sys.version}")
    return True

def check_package_installed(package_name):
    """Check if a package is installed."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_packages(requirements_path: Path):
    """Install packages from requirements.txt."""
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        return False

    logger.info(f"Installing packages from {requirements_path}...")
    try:
        # Use --no-cache-dir to save space on constrained runners
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path),
            "--no-cache-dir", "--upgrade"
        ])
        logger.info("Package installation successful.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {e}")
        return False

def verify_cpu_only():
    """Verify that CUDA is not detected and packages are running in CPU mode."""
    logger.info("Verifying CPU-only environment...")
    
    # Check PyTorch
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available. Forcing CPU usage as per project constraints.")
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        else:
            logger.info("PyTorch: CUDA not available (CPU mode).")
    except ImportError:
        logger.error("PyTorch not installed. Cannot verify CPU mode.")
        return False

    # Check PyBullet (headless by default usually, but verify)
    try:
        import pybullet
        # PyBullet doesn't have a direct 'is_cuda' flag in standard usage,
        # but we ensure we don't try to load GPU plugins.
        logger.info("PyBullet: Imported successfully (headless/CPU).")
    except ImportError:
        logger.error("PyBullet not installed.")
        return False

    # Check MuJoCo
    try:
        import mujoco
        logger.info("MuJoCo: Imported successfully.")
    except ImportError:
        logger.error("MuJoCo not installed.")
        return False

    return True

def verify_imports():
    """Verify all critical imports from requirements.txt."""
    critical_packages = [
        "torch", "diffusers", "transformers", "pybullet", "mujoco",
        "opencv", "pandas", "numpy", "requests", "sklearn", "yaml"
    ]
    
    missing = []
    for pkg in critical_packages:
        try:
            importlib.import_module(pkg)
            logger.debug(f"Package {pkg} imported successfully.")
        except ImportError:
            missing.append(pkg)
    
    if missing:
        logger.error(f"Missing critical packages: {missing}")
        return False
    
    logger.info("All critical packages verified.")
    return True

def main():
    """Main entry point for environment setup."""
    project_root = Path(__file__).parent
    requirements_path = project_root / "requirements.txt"

    if not check_python_version():
        sys.exit(1)

    if not install_packages(requirements_path):
        sys.exit(1)

    if not verify_cpu_only():
        sys.exit(1)

    if not verify_imports():
        sys.exit(1)

    logger.info("Environment setup completed successfully.")

if __name__ == "__main__":
    main()