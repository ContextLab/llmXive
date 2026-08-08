"""
Environment validation script for llmXive Physics Filter pipeline.

This module ensures that PyBullet, MuJoCo, and PyTorch are running in CPU-only modes
and that no CUDA devices are detected. It is critical for maintaining the scientific
integrity of the pipeline by preventing accidental GPU usage on CPU-only runners.
"""

import sys
import subprocess
import importlib
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging for this module
logger = logging.getLogger(__name__)

def check_package_installed(package_name: str) -> bool:
    """
    Check if a package is installed in the current environment.
    
    Args:
        package_name: Name of the package to check.
        
    Returns:
        True if the package is installed, False otherwise.
    """
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_packages(packages: List[str]) -> None:
    """
    Install packages if they are not already installed.
    
    Args:
        packages: List of package names to install.
    """
    for package in packages:
        if not check_package_installed(package):
            logger.info(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def verify_pybullet_cpu_only() -> Tuple[bool, str]:
    """
    Verify that PyBullet is installed and can run in headless/CPU mode.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    package_name = "pybullet"
    if not check_package_installed(package_name):
        return False, f"{package_name} is not installed."
    
    try:
        import pybullet as p
        
        # Check if we can connect in direct mode (headless)
        # This ensures we don't require a display
        p.connect(p.DIRECT)
        p.disconnect()
        
        # PyBullet is inherently CPU-only for simulation, but we verify it runs
        logger.info("PyBullet is installed and running in headless (CPU) mode.")
        return True, "PyBullet is correctly configured for CPU-only simulation."
        
    except Exception as e:
        error_msg = f"PyBullet failed to initialize: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def verify_mujoco_cpu_only() -> Tuple[bool, str]:
    """
    Verify that MuJoCo is installed and configured for CPU-only usage.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    package_name = "mujoco"
    if not check_package_installed(package_name):
        return False, f"{package_name} is not installed."
    
    try:
        import mujoco
        
        # MuJoCo is CPU-only by default in recent versions unless explicitly using GPU
        # We verify it can load a simple model without GPU errors
        # Create a minimal XML string for a free-falling box
        xml_data = """
        <mujoco>
          <worldbody>
            <body name="box" pos="0 0 1">
              <geom type="box" size="0.1 0.1 0.1" mass="1"/>
            </body>
          </worldbody>
        </mujoco>
        """
        
        model = mujoco.MjModel.from_xml_string(xml_data)
        data = mujoco.MjData(model)
        
        # Run a single step to ensure it works
        mujoco.mj_step(model, data)
        
        logger.info("MuJoCo is installed and running in CPU mode.")
        return True, "MuJoCo is correctly configured for CPU-only simulation."
        
    except Exception as e:
        error_msg = f"MuJoCo failed to initialize: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def verify_pytorch_cpu_only() -> Tuple[bool, str]:
    """
    Verify that PyTorch is installed and running in CPU-only mode.
    Ensures no CUDA devices are detected.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    package_name = "torch"
    if not check_package_installed(package_name):
        return False, f"{package_name} is not installed."
    
    try:
        import torch
        
        # Check CUDA availability
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            error_msg = f"CUDA is available with {device_count} device(s). This pipeline requires CPU-only mode."
            logger.error(error_msg)
            return False, error_msg
        
        # Verify we can create a tensor on CPU
        x = torch.tensor([1.0, 2.0, 3.0])
        if x.device.type != "cpu":
            error_msg = f"Tensor device is {x.device.type}, expected 'cpu'."
            logger.error(error_msg)
            return False, error_msg
        
        logger.info("PyTorch is installed and running in CPU-only mode.")
        return True, "PyTorch is correctly configured for CPU-only execution."
        
    except Exception as e:
        error_msg = f"PyTorch verification failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def verify_cpu_only_environment() -> bool:
    """
    Run all environment verification checks.
    
    Returns:
        True if all checks pass, False otherwise.
    """
    logger.info("Starting environment verification for CPU-only pipeline...")
    
    checks = [
        ("PyBullet", verify_pybullet_cpu_only),
        ("MuJoCo", verify_mujoco_cpu_only),
        ("PyTorch", verify_pytorch_cpu_only),
    ]
    
    all_passed = True
    for name, check_func in checks:
        success, message = check_func()
        if success:
            logger.info(f"✓ {name}: {message}")
        else:
            logger.error(f"✗ {name}: {message}")
            all_passed = False
    
    if all_passed:
        logger.info("Environment verification PASSED. All components are CPU-only.")
    else:
        logger.error("Environment verification FAILED. Please resolve the issues above.")
    
    return all_passed

def main() -> int:
    """
    Main entry point for the environment verification script.
    
    Returns:
        Exit code: 0 if verification passes, 1 otherwise.
    """
    # Setup basic logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    success = verify_cpu_only_environment()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())