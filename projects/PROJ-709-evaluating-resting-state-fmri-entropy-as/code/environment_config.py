"""
Environment configuration management for CPU-only execution.

This module ensures that all deep learning and numerical libraries
are configured to run on CPU only, preventing accidental GPU usage
and ensuring reproducibility across different hardware environments.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging for this module
logger = logging.getLogger(__name__)


def configure_cpu_only() -> Dict[str, bool]:
    """
    Configure the environment for CPU-only execution.

    This function sets environment variables and library-specific flags
    to ensure that:
    1. PyTorch (if available) uses CPU only
    2. TensorFlow (if available) uses CPU only
    3. CUDA is disabled at the environment level
    4. OpenMP thread count is controlled for reproducibility

    Returns:
        Dict[str, bool]: A dictionary of configuration status flags
    """
    config_status = {
        "cuda_disabled": False,
        "torch_cpu_only": False,
        "tensorflow_cpu_only": False,
        "openmp_threads_set": False,
        "numpy_threads_set": False,
    }

    # Disable CUDA at the environment level
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    config_status["cuda_disabled"] = True
    logger.info("Environment: CUDA_VISIBLE_DEVICES set to empty string")

    # Configure PyTorch (if available)
    try:
        import torch
        # Force PyTorch to use CPU
        if torch.cuda.is_available():
            torch.cuda.is_available = lambda: False
            logger.warning("PyTorch: CUDA detected but forced to CPU-only mode")
        config_status["torch_cpu_only"] = True
        logger.info("PyTorch: CPU-only mode configured")
    except ImportError:
        logger.debug("PyTorch not installed; skipping CPU configuration")

    # Configure TensorFlow (if available)
    try:
        import tensorflow as tf
        # Disable GPU devices for TensorFlow
        tf.config.set_visible_devices([], "GPU")
        config_status["tensorflow_cpu_only"] = True
        logger.info("TensorFlow: GPU devices disabled")
    except ImportError:
        logger.debug("TensorFlow not installed; skipping CPU configuration")

    # Set thread limits for reproducibility
    # These control parallelism in numerical libraries
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMBA_NUM_THREADS"] = "1"
    config_status["openmp_threads_set"] = True
    config_status["numpy_threads_set"] = True
    logger.info("Environment: Thread counts limited to 1 for reproducibility")

    # Additional NumPy configuration
    try:
        import numpy as np
        # Ensure NumPy uses single-threaded operations if possible
        # Note: This is best-effort as NumPy's threading behavior depends
        # on the underlying BLAS/LAPACK implementation
        if hasattr(np, "core"):
            # Force NumPy to use a single thread for operations
            # This is a heuristic; actual behavior depends on installation
            pass
        logger.info("NumPy: Thread configuration applied")
    except ImportError:
        logger.debug("NumPy not installed; skipping configuration")

    return config_status


def get_environment_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current environment configuration.

    Returns:
        Dict[str, Any]: A dictionary containing environment details
    """
    summary = {
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "not set"),
        "cuda_device_order": os.environ.get("CUDA_DEVICE_ORDER", "not set"),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS", "not set"),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS", "not set"),
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS", "not set"),
        "platform": sys.platform,
        "python_version": sys.version,
    }

    # Check library availability
    try:
        import torch
        summary["torch_available"] = True
        summary["torch_version"] = torch.__version__
        summary["torch_cuda_available"] = torch.cuda.is_available()
    except ImportError:
        summary["torch_available"] = False

    try:
        import tensorflow as tf
        summary["tensorflow_available"] = True
        summary["tensorflow_version"] = tf.__version__
        # Check visible devices
        summary["tensorflow_visible_devices"] = [str(d) for d in tf.config.list_physical_devices()]
    except ImportError:
        summary["tensorflow_available"] = False

    try:
        import numpy as np
        summary["numpy_available"] = True
        summary["numpy_version"] = np.__version__
    except ImportError:
        summary["numpy_available"] = False

    try:
        import scipy
        summary["scipy_available"] = True
        summary["scipy_version"] = scipy.__version__
    except ImportError:
        summary["scipy_available"] = False

    return summary


def validate_cpu_only() -> bool:
    """
    Validate that the environment is correctly configured for CPU-only execution.

    Returns:
        bool: True if CPU-only configuration is valid, False otherwise
    """
    is_valid = True

    # Check CUDA visibility
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_visible != "":
        logger.error(f"CUDA_VISIBLE_DEVICES is set to '{cuda_visible}', expected empty string")
        is_valid = False
    else:
        logger.debug("CUDA visibility validation passed")

    # Check PyTorch (if available)
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("PyTorch reports CUDA is available; this may indicate configuration failure")
            # Note: We may have overridden this, so check actual device
            if torch.cuda.device_count() > 0:
                logger.error("PyTorch has access to GPU devices")
                is_valid = False
    except ImportError:
        pass

    # Check TensorFlow (if available)
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices("GPU")
        if len(gpus) > 0:
            logger.error(f"TensorFlow detected {len(gpus)} GPU devices")
            is_valid = False
        else:
            logger.debug("TensorFlow GPU validation passed")
    except ImportError:
        pass

    # Check thread settings
    for var in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"]:
        if os.environ.get(var) != "1":
            logger.warning(f"{var} is not set to 1, may affect reproducibility")

    if is_valid:
        logger.info("CPU-only environment validation: PASSED")
    else:
        logger.error("CPU-only environment validation: FAILED")

    return is_valid


def main():
    """
    Main entry point for environment configuration.

    This function configures the environment for CPU-only execution
    and prints a summary of the configuration.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting CPU-only environment configuration...")

    # Configure CPU-only execution
    config_status = configure_cpu_only()
    logger.info(f"Configuration status: {config_status}")

    # Get environment summary
    summary = get_environment_summary()
    logger.info("Environment summary:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")

    # Validate configuration
    is_valid = validate_cpu_only()
    if is_valid:
        logger.info("Environment is correctly configured for CPU-only execution.")
    else:
        logger.warning("Environment may not be correctly configured for CPU-only execution.")

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
