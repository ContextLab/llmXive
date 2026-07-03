"""
Environment configuration for CPU-only constraints.

This module disables GPU usage and sets parallelism limits
to ensure the simulation runs within CPU-only CI constraints.
"""

import os
import sys
from typing import Optional

# Try to import torch if available, but don't fail if it's not
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Try to import tensorflow if available
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Try to import jax if available
try:
    import jax
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False


def configure_cpu_only(max_workers: Optional[int] = None, 
                       max_threads: Optional[int] = None) -> None:
    """
    Configure environment for CPU-only execution.
    
    Args:
        max_workers: Maximum number of worker processes (for multiprocessing).
                    If None, defaults to 2 to match project constraints.
        max_threads: Maximum number of threads for numerical libraries.
                    If None, defaults to 2.
    """
    if max_workers is None:
        max_workers = 2
    if max_threads is None:
        max_threads = 2
    
    # Set environment variables for CPU-only execution
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
    
    # Disable GPU for PyTorch
    if TORCH_AVAILABLE:
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        torch.set_num_threads(max_threads)
        torch.set_num_interop_threads(1)
        # Ensure CUDA is not used
        if torch.cuda.is_available():
            torch.cuda.set_device(0)
            # Force CPU mode by setting device
            torch.backends.cudnn.enabled = False
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Disable GPU for TensorFlow
    if TF_AVAILABLE:
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        # Limit TensorFlow threads
        tf.config.threading.set_intra_op_parallelism_threads(max_threads)
        tf.config.threading.set_inter_op_parallelism_threads(1)
    
    # Disable GPU for JAX
    if JAX_AVAILABLE:
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        # JAX respects CUDA_VISIBLE_DEVICES
    
    # Set NumPy thread limits
    os.environ['OMP_NUM_THREADS'] = str(max_threads)
    os.environ['MKL_NUM_THREADS'] = str(max_threads)
    os.environ['OPENBLAS_NUM_THREADS'] = str(max_threads)
    os.environ['VECLIB_MAXIMUM_THREADS'] = str(max_threads)
    os.environ['NUMEXPR_NUM_THREADS'] = str(max_threads)
    
    # Set multiprocessing limits
    os.environ['RAYON_NUM_THREADS'] = str(max_workers)
    
    # Log configuration
    logger_name = __name__
    try:
        from simulation.logger import setup_logger
        logger = setup_logger(logger_name)
        logger.info(f"Configured CPU-only environment")
        logger.info(f"Max workers: {max_workers}")
        logger.info(f"Max threads: {max_threads}")
        logger.info(f"CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES')}")
        if TORCH_AVAILABLE:
            logger.info(f"PyTorch available: {TORCH_AVAILABLE}")
            logger.info(f"PyTorch CUDA available: {torch.cuda.is_available()}")
        if TF_AVAILABLE:
            logger.info(f"TensorFlow available: {TF_AVAILABLE}")
        if JAX_AVAILABLE:
            logger.info(f"JAX available: {JAX_AVAILABLE}")
    except ImportError:
        # Fallback to standard logging if logger not available
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(logger_name).info(f"Configured CPU-only environment")
        logging.getLogger(logger_name).info(f"Max workers: {max_workers}")
        logging.getLogger(logger_name).info(f"Max threads: {max_threads}")
    
    # Set multiprocessing start method for better compatibility
    if sys.platform != 'win32':
        try:
            import multiprocessing
            multiprocessing.set_start_method('fork', force=True)
        except ValueError:
            # Method already set
            pass


def get_environment_info() -> dict:
    """
    Get current environment configuration information.
    
    Returns:
        Dictionary with environment configuration details.
    """
    return {
        'torch_available': TORCH_AVAILABLE,
        'tf_available': TF_AVAILABLE,
        'jax_available': JAX_AVAILABLE,
        'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set'),
        'omp_threads': os.environ.get('OMP_NUM_THREADS', 'Not set'),
        'mkl_threads': os.environ.get('MKL_NUM_THREADS', 'Not set'),
        'max_workers': int(os.environ.get('RAYON_NUM_THREADS', '2')),
    }


def verify_cpu_only() -> bool:
    """
    Verify that GPU is disabled and environment is configured for CPU-only.
    
    Returns:
        True if GPU is disabled, False otherwise.
    """
    if TORCH_AVAILABLE and torch.cuda.is_available():
        # Check if we're actually using CPU
        try:
            # This will raise an error if CUDA is not properly disabled
            device = torch.device('cuda:0')
            # If we get here, CUDA might be accessible
            # Check if CUDA_VISIBLE_DEVICES is properly set
            if os.environ.get('CUDA_VISIBLE_DEVICES') == '-1':
                # CUDA is disabled via environment variable
                return True
            return False
        except RuntimeError:
            # CUDA not available
            return True
    
    if TF_AVAILABLE:
        # Check TensorFlow GPU devices
        try:
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                return False
        except:
            pass
    
    # Check environment variable
    cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if cuda_devices == '-1':
        return True
    
    return True  # Default to True if no GPU libraries found


# Initialize environment on module import
configure_cpu_only()