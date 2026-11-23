"""
Environment configuration management for CPU-only execution.
Ensures no CUDA flags are set and forces CPU-only execution for PyTorch/TensorFlow.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def configure_cpu_only() -> Dict[str, str]:
    """
    Configure environment variables to enforce CPU-only execution.
    Disables CUDA, sets thread limits, and clears GPU visibility.

    Returns:
        Dict[str, str]: Dictionary of configured environment variables.
    """
    config = {}

    # PyTorch: Force CPU
    if 'PYTORCH_NO_CUDA' not in os.environ:
        os.environ['PYTORCH_NO_CUDA'] = '1'
        config['PYTORCH_NO_CUDA'] = '1'
        logger.info("Set PYTORCH_NO_CUDA=1 to disable CUDA")

    # TensorFlow: Disable GPU
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        config['CUDA_VISIBLE_DEVICES'] = ''
        logger.info("Set CUDA_VISIBLE_DEVICES='' to hide GPUs from TensorFlow")

    # General CUDA visibility (for any other libraries)
    if 'CUDA_VISIBLE_DEVICES' not in os.environ or os.environ.get('CUDA_VISIBLE_DEVICES', '') != '':
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        config['CUDA_VISIBLE_DEVICES'] = ''

    # Limit number of threads to prevent CPU oversubscription
    if 'OMP_NUM_THREADS' not in os.environ:
        os.environ['OMP_NUM_THREADS'] = '4'
        config['OMP_NUM_THREADS'] = '4'
        logger.info("Set OMP_NUM_THREADS=4 for thread control")

    if 'MKL_NUM_THREADS' not in os.environ:
        os.environ['MKL_NUM_THREADS'] = '4'
        config['MKL_NUM_THREADS'] = '4'

    if 'NUMEXPR_NUM_THREADS' not in os.environ:
        os.environ['NUMEXPR_NUM_THREADS'] = '4'
        config['NUMEXPR_NUM_THREADS'] = '4'

    if 'OPENBLAS_NUM_THREADS' not in os.environ:
        os.environ['OPENBLAS_NUM_THREADS'] = '4'
        config['OPENBLAS_NUM_THREADS'] = '4'

    return config

def get_environment_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current environment configuration.

    Returns:
        Dict[str, Any]: Summary including CPU/GPU status and key env vars.
    """
    import platform
    try:
        import torch
        cuda_available = torch.cuda.is_available()
    except ImportError:
        cuda_available = False
        torch_installed = False
    else:
        torch_installed = True

    try:
        import tensorflow as tf
        tf_gpus = tf.config.list_physical_devices('GPU')
    except ImportError:
        tf_gpus = []
        tf_installed = False
    else:
        tf_installed = True

    summary = {
        'platform': platform.system(),
        'python_version': platform.python_version(),
        'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES', 'default'),
        'pytorch_no_cuda': os.environ.get('PYTORCH_NO_CUDA', '0'),
        'torch_installed': torch_installed,
        'torch_cuda_available': cuda_available if torch_installed else None,
        'tensorflow_installed': tf_installed,
        'tensorflow_gpus_visible': len(tf_gpus) if tf_installed else None,
        'cpu_threads': {
            'OMP': os.environ.get('OMP_NUM_THREADS', 'default'),
            'MKL': os.environ.get('MKL_NUM_THREADS', 'default'),
            'NUMEXPR': os.environ.get('NUMEXPR_NUM_THREADS', 'default'),
            'OPENBLAS': os.environ.get('OPENBLAS_NUM_THREADS', 'default'),
        }
    }

    return summary

def validate_cpu_only() -> bool:
    """
    Validate that the environment is correctly configured for CPU-only execution.
    Checks that CUDA is disabled in PyTorch and TensorFlow.

    Returns:
        bool: True if CPU-only mode is validated, False otherwise.
    """
    is_valid = True

    # Check PyTorch
    try:
        import torch
        if torch.cuda.is_available():
            logger.error("CUDA is available in PyTorch but should be disabled!")
            is_valid = False
        else:
            logger.info("PyTorch: CUDA disabled (CPU-only confirmed)")
    except ImportError:
        logger.warning("PyTorch not installed; skipping CUDA check")

    # Check TensorFlow
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            logger.error(f"TensorFlow sees {len(gpus)} GPU(s) but should be CPU-only!")
            is_valid = False
        else:
            logger.info("TensorFlow: No GPUs visible (CPU-only confirmed)")
    except ImportError:
        logger.warning("TensorFlow not installed; skipping GPU check")

    # Check environment variables
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        logger.warning("CUDA_VISIBLE_DEVICES is not set to empty string")
        is_valid = False

    if os.environ.get('PYTORCH_NO_CUDA') != '1':
        logger.warning("PYTORCH_NO_CUDA is not set to '1'")
        is_valid = False

    return is_valid

def main():
    """Main entry point to configure and validate CPU-only environment."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Configuring CPU-only execution environment...")
    configure_cpu_only()

    logger.info("\n--- Environment Summary ---")
    summary = get_environment_summary()
    for key, value in summary.items():
        logger.info(f"{key}: {value}")

    logger.info("\n--- Validation ---")
    is_valid = validate_cpu_only()
    if is_valid:
        logger.info("SUCCESS: Environment is correctly configured for CPU-only execution.")
    else:
        logger.warning("WARNING: Environment validation failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()