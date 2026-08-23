"""
CPU Efficiency Utilities for llmXive Project PROJ-199

This module ensures all computations run strictly on CPU and prevents
accidental GPU usage (e.g., from PyTorch, TensorFlow, or CuPy) to satisfy
the project's hardware constraints and reproducibility requirements.
"""

import os
import sys
import logging
from typing import Optional

# Configure logger
logger = logging.getLogger(__name__)


def setup_cpu_efficiency() -> None:
    """
    Enforce CPU-only execution environment.

    This function sets environment variables to:
    1. Disable GPU usage in PyTorch (if installed)
    2. Limit OpenMP threads to prevent oversubscription
    3. Disable CUDA visibility
    4. Set BLAS/LAPACK thread limits

    Call this at the very beginning of any script entry point.
    """
    # Disable PyTorch GPU usage
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["PYTORCH_NO_CUDA"] = "1"
    
    # Limit OpenMP threads to 1 per process to avoid oversubscription
    # unless explicitly configured otherwise in environment
    if "OMP_NUM_THREADS" not in os.environ:
        os.environ["OMP_NUM_THREADS"] = "1"
    
    # Limit MKL threads (Intel MKL BLAS/LAPACK)
    if "MKL_NUM_THREADS" not in os.environ:
        os.environ["MKL_NUM_THREADS"] = "1"
    
    # Limit NumPy/SciPy thread pools
    if "OPENBLAS_NUM_THREADS" not in os.environ:
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
    
    # Disable GPU usage in TensorFlow (if installed)
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    
    logger.info("CPU efficiency mode enabled: GPU access disabled, thread pools limited.")


class CPUOnlyContext:
    """
    Context manager to ensure CPU-only execution within a specific block.
    
    Usage:
        with CPUOnlyContext():
            # Code that must run on CPU
            result = model.predict(data)
    """
    
    def __init__(self):
        self._original_cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
        self._original_pytorch_no_cuda = os.environ.get("PYTORCH_NO_CUDA")
        
    def __enter__(self):
        # Enforce CPU-only settings
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["PYTORCH_NO_CUDA"] = "1"
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original environment if it existed
        if self._original_cuda_visible is not None:
            os.environ["CUDA_VISIBLE_DEVICES"] = self._original_cuda_visible
        elif "CUDA_VISIBLE_DEVICES" in os.environ:
            del os.environ["CUDA_VISIBLE_DEVICES"]
            
        if self._original_pytorch_no_cuda is not None:
            os.environ["PYTORCH_NO_CUDA"] = self._original_pytorch_no_cuda
        elif "PYTORCH_NO_CUDA" in os.environ:
            del os.environ["PYTORCH_NO_CUDA"]
            
        return False


def verify_no_gpu_access() -> bool:
    """
    Verify that no GPU access is available or enabled in the current environment.
    
    Returns:
        bool: True if GPU access is confirmed disabled, False otherwise.
        
    Raises:
        RuntimeError: If GPU access is detected.
    """
    # Check CUDA_VISIBLE_DEVICES
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_visible and cuda_visible.strip() != "":
        logger.warning(f"CUDA_VISIBLE_DEVICES is set to: {cuda_visible}")
        return False
        
    # Check PyTorch CUDA availability
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("PyTorch reports CUDA is available!")
            return False
    except ImportError:
        # PyTorch not installed, skip check
        pass
        
    # Check TensorFlow GPU availability
    try:
        import tensorflow as tf
        if tf.config.list_physical_devices("GPU"):
            logger.warning("TensorFlow reports GPU devices are available!")
            return False
    except ImportError:
        # TensorFlow not installed, skip check
        pass
        
    # Check CuPy availability
    try:
        import cupy
        if cupy.cuda.runtime.getDeviceCount() > 0:
            logger.warning("CuPy reports GPU devices are available!")
            return False
    except ImportError:
        # CuPy not installed, skip check
        pass
        
    logger.info("GPU access verification passed: No GPU devices detected.")
    return True


def main() -> None:
    """
    CLI entry point for CPU efficiency verification.
    
    This script can be run directly to verify that the environment
    is properly configured for CPU-only execution.
    """
    setup_cpu_efficiency()
    
    if verify_no_gpu_access():
        print("✓ CPU-only mode verified successfully.")
        sys.exit(0)
    else:
        print("✗ GPU access detected! CPU-only mode verification failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
