"""
Environment validation script for llmXive Physics Filter.
Ensures PyBullet, MuJoCo, and PyTorch are running in CPU-only mode
and that no CUDA devices are detected.
"""

import sys
import subprocess
import importlib
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


def install_packages(package_names: List[str]) -> None:
    """Install packages if they are not installed."""
    for package in package_names:
        if not check_package_installed(package):
            logger.info(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {e}")
                raise


def verify_pybullet_cpu_only() -> Tuple[bool, str]:
    """
    Verify PyBullet is available and running in CPU-only mode.
    Returns (success, message).
    """
    package_name = "pybullet"
    if not check_package_installed(package_name):
        return False, f"{package_name} is not installed"

    try:
        import pybullet as p

        # Check if we can connect to a headless physics server
        # This implicitly verifies CPU mode as PyBullet is CPU-bound by default
        # unless explicitly linked with GPU physics (which we don't use here)
        client_id = p.connect(p.DIRECT)
        
        if client_id == -1:
            return False, "Failed to connect to PyBullet physics server"
        
        # Verify basic functionality
        p.setGravity(0, 0, -9.81)
        p.stepSimulation()
        p.disconnect(client_id)
        
        return True, "PyBullet is running in CPU-only mode (headless)"
    except Exception as e:
        return False, f"PyBullet verification failed: {str(e)}"


def verify_mujoco_cpu_only() -> Tuple[bool, str]:
    """
    Verify MuJoCo is available and running in CPU-only mode.
    Returns (success, message).
    """
    package_name = "mujoco"
    if not check_package_installed(package_name):
        return False, f"{package_name} is not installed"

    try:
        import mujoco
        
        # MuJoCo is CPU-only by default in its Python bindings
        # We verify it can load a minimal model
        model_data = b"""
        <mujoco>
        <worldbody>
            <body name="root">
                <geom type="box" size="1 1 1" rgba="1 0 0 1"/>
            </body>
        </worldbody>
        </mujoco>
        """
        
        model = mujoco.MjModel.from_xml_string(model_data.decode('utf-8'))
        data = mujoco.MjData(model)
        
        # Step simulation
        mujoco.mj_step(model, data)
        
        return True, "MuJoCo is running in CPU-only mode"
    except Exception as e:
        return False, f"MuJoCo verification failed: {str(e)}"


def verify_pytorch_cpu_only() -> Tuple[bool, str]:
    """
    Verify PyTorch is installed and running in CPU-only mode.
    Ensures no CUDA is detected.
    Returns (success, message).
    """
    package_name = "torch"
    if not check_package_installed(package_name):
        return False, f"{package_name} is not installed"

    try:
        import torch
        
        # Check CUDA availability
        if torch.cuda.is_available():
            cuda_device_count = torch.cuda.device_count()
            if cuda_device_count > 0:
                return False, f"CUDA is available with {cuda_device_count} device(s). " \
                              f"Ensure CPU-only PyTorch is installed (pip install torch --index-url https://download.pytorch.org/whl/cpu)"
        
        # Verify we can create a tensor on CPU
        test_tensor = torch.tensor([1.0, 2.0, 3.0])
        if test_tensor.is_cuda:
            return False, "Tensor was created on CUDA device instead of CPU"
        
        # Verify basic computation
        result = test_tensor * 2
        expected = torch.tensor([2.0, 4.0, 6.0])
        
        if not torch.allclose(result, expected):
            return False, "PyTorch computation failed"
        
        return True, "PyTorch is running in CPU-only mode"
    except Exception as e:
        return False, f"PyTorch verification failed: {str(e)}"


def verify_cpu_only_environment() -> bool:
    """
    Verify the entire environment is CPU-only.
    Runs all checks and returns True if all pass, False otherwise.
    """
    logger.info("Starting environment validation for CPU-only mode...")
    
    checks = [
        ("PyBullet", verify_pybullet_cpu_only),
        ("MuJoCo", verify_mujoco_cpu_only),
        ("PyTorch", verify_pytorch_cpu_only),
    ]
    
    all_passed = True
    results = []
    
    for name, check_func in checks:
        success, message = check_func()
        results.append((name, success, message))
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {name} - {message}")
        
        if not success:
            all_passed = False
    
    logger.info("-" * 60)
    if all_passed:
        logger.info("All environment checks PASSED. CPU-only mode confirmed.")
    else:
        failed_checks = [name for name, success, _ in results if not success]
        logger.error(f"Environment validation FAILED. Failed checks: {', '.join(failed_checks)}")
    
    return all_passed


def main() -> int:
    """
    Main entry point for the environment validation script.
    Returns 0 if all checks pass, 1 otherwise.
    """
    try:
        success = verify_cpu_only_environment()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())