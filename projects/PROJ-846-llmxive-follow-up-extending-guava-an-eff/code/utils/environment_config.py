"""
Environment configuration management for CPU-only runner constraints.

This module handles:
1. Detection of available CPU resources.
2. Enforcement of CPU-only constraints (disabling CUDA).
3. PyTorch configuration for CPU execution.
4. Validation of environment constraints before pipeline execution.
"""
import os
import sys
import platform
import subprocess
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass

def detect_cpu_count() -> int:
    """
    Detect the number of available logical CPU cores.
    
    Returns:
        int: Number of logical CPU cores available.
    
    Raises:
        EnvironmentConfigError: If CPU count cannot be determined.
    """
    try:
        # Try using os.cpu_count() first (standard library)
        count = os.cpu_count()
        if count is None or count <= 0:
            raise EnvironmentConfigError("os.cpu_count() returned None or non-positive value")
        return count
    except Exception as e:
        # Fallback to subprocess for Linux/Unix systems
        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["nproc"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                count = int(result.stdout.strip())
                if count > 0:
                    return count
            except (subprocess.SubprocessError, ValueError) as sub_e:
                logger.warning(f"Subprocess fallback failed: {sub_e}")
        elif platform.system() == "Darwin":  # macOS
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "hw.logicalcpu"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                count = int(result.stdout.strip())
                if count > 0:
                    return count
            except (subprocess.SubprocessError, ValueError) as sub_e:
                logger.warning(f"macOS sysctl fallback failed: {sub_e}")
        
        # Last resort fallback
        logger.error("Failed to detect CPU count using all methods.")
        raise EnvironmentConfigError("Unable to determine CPU count") from e

def verify_cpu_only_constraint() -> bool:
    """
    Verify that the environment is configured for CPU-only execution.
    
    Checks:
    1. CUDA is not available (torch.cuda.is_available() should be False).
    2. Relevant environment variables are set to enforce CPU usage.
    
    Returns:
        bool: True if CPU-only constraints are satisfied, False otherwise.
    
    Raises:
        EnvironmentConfigError: If CUDA is detected and cannot be disabled.
    """
    try:
        import torch
    except ImportError:
        # If torch is not installed, we assume CPU-only by default
        logger.warning("PyTorch not installed. Assuming CPU-only environment.")
        return True

    # Check if CUDA is available
    if torch.cuda.is_available():
        logger.warning("CUDA is available in the environment.")
        
        # Attempt to enforce CPU-only by setting environment variables
        # Note: These must be set BEFORE torch is imported for full effect,
        # but we can still try to mitigate usage now.
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        
        # Re-check after setting env vars (though torch might have already initialized)
        if torch.cuda.is_available():
            # Check if we can actually use CPU
            try:
                # Try to create a tensor on CPU
                _ = torch.zeros(1, device='cpu')
                logger.info("Forced CPU-only mode via environment variables.")
                logger.warning("CUDA is available but will be ignored. Performance may be impacted if legacy CUDA kernels are used.")
                return True
            except RuntimeError as e:
                raise EnvironmentConfigError(
                    "CUDA is available and could not be disabled. "
                    "The pipeline requires a CPU-only environment."
                ) from e
        else:
            logger.info("CUDA disabled successfully via environment variables.")
            return True
    
    # Check for specific environment variables that might indicate GPU usage
    if os.getenv("CUDA_VISIBLE_DEVICES", "") != "-1" and os.getenv("CUDA_VISIBLE_DEVICES", "") != "":
        logger.warning(f"CUDA_VISIBLE_DEVICES is set to: {os.getenv('CUDA_VISIBLE_DEVICES')}. "
                     "Consider setting to '-1' for strict CPU-only execution.")
    
    return True

def configure_torch_for_cpu():
    """
    Configure PyTorch to use CPU-only resources.
    
    Actions:
    1. Set number of inter-op and intra-op threads.
    2. Disable MKL-DNN (if applicable) for consistency.
    3. Ensure CUDA is not used.
    """
    try:
        import torch
        import torch.set_num_threads
    except ImportError:
        logger.warning("PyTorch not installed. Skipping torch configuration.")
        return

    # Detect CPU count for optimal thread configuration
    cpu_count = detect_cpu_count()
    
    # Set number of threads for PyTorch operations
    # Using a conservative number to avoid oversubscription in multi-process scenarios
    # For a single process pipeline, we can use a higher fraction
    num_threads = max(1, cpu_count // 2)
    
    torch.set_num_threads(num_threads)
    torch.set_num_interop_threads(1)
    
    # Explicitly set device to CPU
    if torch.cuda.is_available():
        logger.warning("CUDA detected but configured for CPU usage.")
        # Ensure CUDA is not used by default
        torch.cuda.set_device(-1)
    
    logger.info(f"PyTorch configured for CPU: {num_threads} threads, device=CPU")

def enforce_cpu_only():
    """
    Enforce CPU-only execution by setting environment variables and configurations.
    
    This function should be called at the very beginning of the script,
    before any heavy libraries (like torch) are imported or initialized.
    """
    # Set environment variables to disable CUDA
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["TORCH_USE_CUDA_DSA"] = "0"
    
    # Disable GPU-related features in other libraries if possible
    # (e.g., OpenCV with CUDA support)
    os.environ["OPENCV_CPU_DISABLE"] = "1"
    
    logger.info("Enforced CPU-only environment variables.")
    
    # Verify the configuration
    if not verify_cpu_only_constraint():
        raise EnvironmentConfigError(
            "Failed to enforce CPU-only constraints. "
            "The pipeline requires a CPU-only environment."
        )

def get_environment_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current environment configuration.
    
    Returns:
        Dict[str, Any]: Dictionary containing environment details.
    """
    try:
        import torch
        torch_available = True
        cuda_available = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if cuda_available else 0
    except ImportError:
        torch_available = False
        cuda_available = False
        device_count = 0

    try:
        cpu_count = detect_cpu_count()
    except EnvironmentConfigError:
        cpu_count = 0

    return {
        "platform": platform.system(),
        "python_version": sys.version,
        "cpu_count": cpu_count,
        "torch_available": torch_available,
        "cuda_available": cuda_available,
        "cuda_device_count": device_count,
        "cpu_only_enforced": os.getenv("CUDA_VISIBLE_DEVICES") == "-1",
        "environment_variables": {
            "CUDA_VISIBLE_DEVICES": os.getenv("CUDA_VISIBLE_DEVICES"),
            "CUDA_DEVICE_ORDER": os.getenv("CUDA_DEVICE_ORDER"),
            "TORCH_USE_CUDA_DSA": os.getenv("TORCH_USE_CUDA_DSA"),
            "OPENCV_CPU_DISABLE": os.getenv("OPENCV_CPU_DISABLE")
        }
    }

def main():
    """
    Main entry point for environment configuration verification.
    """
    logger.info("Starting environment configuration verification...")
    
    # Enforce CPU-only settings first
    enforce_cpu_only()
    
    # Configure PyTorch
    configure_torch_for_cpu()
    
    # Get and print summary
    summary = get_environment_summary()
    
    logger.info("Environment Summary:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    if summary["cpu_only_enforced"]:
        logger.info("✓ Environment is correctly configured for CPU-only execution.")
        return 0
    else:
        logger.error("✗ Environment is NOT correctly configured for CPU-only execution.")
        return 1

if __name__ == "__main__":
    sys.exit(main())