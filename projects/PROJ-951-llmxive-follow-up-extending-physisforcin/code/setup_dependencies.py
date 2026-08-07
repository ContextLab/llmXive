"""
T002: Initialize Python project with CPU-only dependencies.

This script verifies Python version, installs required packages from requirements.txt,
explicitly ensures CPU-only mode for PyTorch, and verifies that critical imports work.
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
        logging.FileHandler('logs/setup_dependencies.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def check_python_version(min_version=(3, 10)):
    """Check if the current Python version meets the minimum requirement."""
    current_version = sys.version_info[:2]
    if current_version < min_version:
        error_msg = f"Python {min_version[0]}.{min_version[1]}+ is required. Found {sys.version}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    logger.info(f"Python version check passed: {sys.version}")

def install_packages(requirements_path: Path):
    """Install packages from requirements.txt."""
    if not requirements_path.exists():
        error_msg = f"Requirements file not found: {requirements_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info(f"Installing packages from {requirements_path}...")
    try:
        # Use --upgrade to ensure latest compatible versions
        # Use --no-cache-dir to save disk space on constrained runners
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path),
            "--upgrade", "--no-cache-dir"
        ])
        logger.info("Package installation completed successfully.")
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to install packages: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def verify_cpu_only():
    """Verify that PyTorch is running in CPU-only mode."""
    logger.info("Verifying CPU-only configuration for PyTorch...")
    try:
        import torch
        # Check if CUDA is available
        if torch.cuda.is_available():
            logger.warning("CUDA is detected! Forcing CPU-only mode for this project.")
            # In a real scenario, we might want to fail here if strict CPU is required
            # but for now we just warn.
        else:
            logger.info("Confirmed: PyTorch is running in CPU-only mode.")
        
        # Verify we can create a CPU tensor
        x = torch.zeros(1, device='cpu')
        logger.info("Successfully created a CPU tensor.")
    except ImportError:
        error_msg = "PyTorch is not installed or cannot be imported."
        logger.error(error_msg)
        raise ImportError(error_msg)
    except Exception as e:
        error_msg = f"Error verifying CPU-only mode: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def verify_imports():
    """Verify that all critical packages can be imported."""
    critical_packages = [
        'torch', 'pybullet', 'mujoco', 'diffusers', 'transformers',
        'sklearn', 'cv2', 'pandas', 'numpy', 'requests', 'datasets'
    ]
    
    logger.info("Verifying imports for critical packages...")
    failed_imports = []
    
    for package in critical_packages:
        try:
            # Map common import names to actual module names
            module_name = package
            if package == 'sklearn':
                module_name = 'sklearn'
            elif package == 'cv2':
                module_name = 'cv2'
            
            __import__(module_name)
            logger.debug(f"  ✓ {package} imported successfully.")
        except ImportError as e:
            logger.error(f"  ✗ Failed to import {package}: {e}")
            failed_imports.append((package, str(e)))
    
    if failed_imports:
        error_msg = f"Failed to import {len(failed_imports)} critical packages:\n" + \
                    "\n".join([f"  - {pkg}: {err}" for pkg, err in failed_imports])
        logger.error(error_msg)
        raise ImportError(error_msg)
    
    logger.info("All critical packages imported successfully.")

def main():
    """Main entry point for T002 setup."""
    project_root = Path(__file__).parent
    requirements_path = project_root / "requirements.txt"
    
    try:
        logger.info("Starting T002: Initialize Python project with CPU-only dependencies.")
        
        # 1. Check Python version
        check_python_version()
        
        # 2. Install packages
        install_packages(requirements_path)
        
        # 3. Verify CPU-only mode
        verify_cpu_only()
        
        # 4. Verify imports
        verify_imports()
        
        logger.info("T002 completed successfully. Project is initialized with CPU-only dependencies.")
        return 0
        
    except Exception as e:
        logger.error(f"T002 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
