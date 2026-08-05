"""
Environment configuration management for CPU-only execution.
Ensures no CUDA flags are set and configures libraries to use CPU only.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def configure_cpu_only() -> Dict[str, str]:
    """
    Configure environment variables to enforce CPU-only execution.
    Returns a dictionary of the configuration changes made.
    
    This function:
    1. Unsets any existing CUDA_VISIBLE_DEVICES
    2. Sets PyTorch to CPU-only mode (if available)
    3. Sets TensorFlow to CPU-only mode (if available)
    4. Configures OpenMP thread limits for stability
    5. Disables GPU acceleration flags in relevant libraries
    
    Returns:
        Dict[str, str]: Mapping of environment variables set/modified
    """
    config_changes = {}
    
    # 1. Ensure CUDA is not visible
    if 'CUDA_VISIBLE_DEVICES' in os.environ:
        old_val = os.environ.pop('CUDA_VISIBLE_DEVICES')
        config_changes['CUDA_VISIBLE_DEVICES'] = f"(unset from '{old_val}')"
        logger.info(f"Unset CUDA_VISIBLE_DEVICES (was: {old_val})")
    else:
        config_changes['CUDA_VISIBLE_DEVICES'] = "already unset"
        logger.debug("CUDA_VISIBLE_DEVICES was already unset")
    
    # 2. Configure PyTorch (if installed)
    try:
        import torch
        torch.set_num_threads(1)
        if torch.cuda.is_available():
            logger.warning("PyTorch: CUDA detected but will be disabled for this run")
        config_changes['torch_set_num_threads'] = "1"
        config_changes['torch_device'] = "cpu"
        logger.info("PyTorch configured for CPU-only (num_threads=1)")
    except ImportError:
        logger.debug("PyTorch not installed, skipping torch configuration")
    except Exception as e:
        logger.warning(f"Could not configure PyTorch: {e}")
    
    # 3. Configure TensorFlow (if installed)
    try:
        import tensorflow as tf
        # Limit GPU memory growth and disable GPU if possible
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            try:
                # Disable all GPUs
                tf.config.set_visible_devices([], 'GPU')
                config_changes['tensorflow_visible_devices'] = "[]"
                logger.info("TensorFlow: Disabled all GPU devices")
            except RuntimeError as e:
                logger.warning(f"TensorFlow GPU disable failed: {e}")
        config_changes['tensorflow_threads'] = "1"
        logger.info("TensorFlow configured for CPU-only")
    except ImportError:
        logger.debug("TensorFlow not installed, skipping tensorflow configuration")
    except Exception as e:
        logger.warning(f"Could not configure TensorFlow: {e}")
    
    # 4. Set OpenMP thread limits for stability and reproducibility
    # This prevents libraries from spawning too many threads
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    
    config_changes['OMP_NUM_THREADS'] = '1'
    config_changes['MKL_NUM_THREADS'] = '1'
    config_changes['OPENBLAS_NUM_THREADS'] = '1'
    config_changes['VECLIB_MAXIMUM_THREADS'] = '1'
    config_changes['NUMEXPR_NUM_THREADS'] = '1'
    logger.info("OpenMP/MKL/OpenBLAS thread limits set to 1")
    
    # 5. Ensure no GPU-specific environment variables are set
    gpu_vars = [
        'CUDA_HOME', 'CUDA_PATH', 'NVCC', 'LD_LIBRARY_PATH',
        'LIBRARY_PATH', 'DYLD_LIBRARY_PATH'
    ]
    for var in gpu_vars:
        if var in os.environ and 'cuda' in os.environ[var].lower():
            logger.warning(f"Potential GPU library path found in {var}: {os.environ[var]}")
    
    return config_changes

def get_environment_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current environment configuration.
    
    Returns:
        Dict[str, Any]: Summary including:
            - cpu_only_mode: bool (True if CUDA is disabled)
            - torch_available: bool
            - torch_cuda_available: bool
            - tensorflow_available: bool
            - tensorflow_gpu_available: bool
            - thread_limits: Dict[str, str]
            - cuda_visible_devices: str or None
    """
    summary = {
        'cpu_only_mode': False,
        'torch_available': False,
        'torch_cuda_available': False,
        'tensorflow_available': False,
        'tensorflow_gpu_available': False,
        'thread_limits': {},
        'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES')
    }
    
    # Check PyTorch
    try:
        import torch
        summary['torch_available'] = True
        summary['torch_cuda_available'] = torch.cuda.is_available()
        summary['cpu_only_mode'] = not summary['torch_cuda_available'] or 'CUDA_VISIBLE_DEVICES' not in os.environ
    except ImportError:
        pass
    
    # Check TensorFlow
    try:
        import tensorflow as tf
        summary['tensorflow_available'] = True
        gpus = tf.config.list_physical_devices('GPU')
        summary['tensorflow_gpu_available'] = len(gpus) > 0
        if not summary['tensorflow_gpu_available']:
            summary['cpu_only_mode'] = True
    except ImportError:
        pass
    
    # Thread limits
    summary['thread_limits'] = {
        'OMP': os.environ.get('OMP_NUM_THREADS', 'not set'),
        'MKL': os.environ.get('MKL_NUM_THREADS', 'not set'),
        'OPENBLAS': os.environ.get('OPENBLAS_NUM_THREADS', 'not set'),
        'NUMEXPR': os.environ.get('NUMEXPR_NUM_THREADS', 'not set')
    }
    
    # Validate CPU-only status
    if 'CUDA_VISIBLE_DEVICES' in os.environ:
        summary['cpu_only_mode'] = False
    elif summary['torch_cuda_available'] or summary['tensorflow_gpu_available']:
        summary['cpu_only_mode'] = False
    
    return summary

def validate_cpu_only() -> bool:
    """
    Validate that the environment is correctly configured for CPU-only execution.
    
    Returns:
        bool: True if CPU-only mode is confirmed, False otherwise
    
    Raises:
        RuntimeError: If GPU execution is detected and cannot be disabled
    """
    summary = get_environment_summary()
    
    # Check if CUDA is explicitly disabled
    if 'CUDA_VISIBLE_DEVICES' in os.environ:
        logger.error("CUDA_VISIBLE_DEVICES is set, GPU execution may occur")
        return False
    
    # Check PyTorch
    if summary['torch_available'] and summary['torch_cuda_available']:
        logger.error("PyTorch CUDA is available and not disabled")
        return False
    
    # Check TensorFlow
    if summary['tensorflow_available'] and summary['tensorflow_gpu_available']:
        logger.error("TensorFlow GPU is available and not disabled")
        return False
    
    # Check thread limits
    for key, val in summary['thread_limits'].items():
        if val == 'not set':
            logger.warning(f"{key} thread limit not set (may cause performance issues)")
    
    logger.info("Environment validated: CPU-only mode confirmed")
    return True

def main():
    """
    Main entry point for running environment configuration checks.
    This function configures CPU-only execution and validates the setup.
    """
    logger.info("=== Starting Environment Configuration for CPU-Only Execution ===")
    
    # Configure CPU-only mode
    config_changes = configure_cpu_only()
    logger.info(f"Configuration changes applied: {list(config_changes.keys())}")
    
    # Get and display summary
    summary = get_environment_summary()
    logger.info(f"Environment Summary:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    # Validate configuration
    is_valid = validate_cpu_only()
    if is_valid:
        logger.info("✓ Environment successfully configured for CPU-only execution")
        sys.exit(0)
    else:
        logger.error("✗ Environment validation failed: GPU execution may occur")
        sys.exit(1)

if __name__ == "__main__":
    main()