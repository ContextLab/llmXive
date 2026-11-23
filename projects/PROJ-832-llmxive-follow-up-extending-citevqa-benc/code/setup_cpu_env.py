"""
Environment configuration management for CPU-only execution constraints.

This module enforces CPU-only execution by:
1. Setting environment variables to disable GPU usage (CUDA, ROCm, etc.)
2. Configuring PyTorch to use CPU only
3. Validating the environment configuration
4. Providing utilities to check environment constraints
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for CPU-only enforcement
CPU_ONLY_ENV_VARS = {
    'CUDA_VISIBLE_DEVICES': '-1',
    'CUDA_DEVICE_ORDER': 'PCI_BUS_ID',
    'TORCH_USE_CUDA_DSA': '0',
    'HF_HUB_OFFLINE': '0',  # Allow online downloads if needed
    'TRANSFORMERS_OFFLINE': '0',
}

def set_cpu_only_environment() -> Dict[str, str]:
    """
    Set environment variables to enforce CPU-only execution.
    
    Returns:
        Dict[str, str]: The environment variables that were set.
    """
    set_vars = {}
    for var, value in CPU_ONLY_ENV_VARS.items():
        if os.environ.get(var) != value:
            old_value = os.environ.get(var, 'NOT_SET')
            os.environ[var] = value
            set_vars[var] = value
            logger.info(f"Set {var}={value} (was: {old_value})")
        else:
            set_vars[var] = value
    return set_vars

def validate_cpu_only_environment() -> bool:
    """
    Validate that the environment is configured for CPU-only execution.
    
    Returns:
        bool: True if environment is correctly configured for CPU-only, False otherwise.
    """
    errors = []
    
    # Check CUDA_VISIBLE_DEVICES
    cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if cuda_devices != '-1':
        errors.append(f"CUDA_VISIBLE_DEVICES should be '-1', found: {cuda_devices}")
    
    # Check for GPU-related environment variables that should be disabled
    if os.environ.get('CUDA_VISIBLE_DEVICES', '-1') != '-1':
        errors.append("CUDA is still visible despite CPU-only configuration")
    
    # Check PyTorch availability and device
    try:
        import torch
        if torch.cuda.is_available():
            errors.append("PyTorch reports CUDA is available - this should be disabled in CPU-only mode")
        else:
            logger.info("PyTorch correctly reports CUDA is not available")
    except ImportError:
        logger.warning("PyTorch not installed - skipping CUDA check")
    except Exception as e:
        logger.warning(f"Error checking PyTorch CUDA availability: {e}")
    
    if errors:
        logger.error("CPU-only environment validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("CPU-only environment validation passed")
    return True

def get_cpu_config() -> Dict[str, Any]:
    """
    Get configuration dictionary for CPU-only execution.
    
    Returns:
        Dict[str, Any]: Configuration dictionary with CPU-specific settings.
    """
    return {
        'device': 'cpu',
        'num_workers': 0,  # Disable multiprocessing workers for CPU safety
        'pin_memory': False,
        'cuda': False,
        'mps': False,  # Disable MPS (Apple Silicon) for strict CPU-only
        'xla': False,
    }

def configure_pytorch_cpu_only() -> None:
    """
    Configure PyTorch to use CPU only and disable GPU acceleration.
    
    This must be called before importing or using any PyTorch models.
    """
    try:
        import torch
        
        # Force CPU device
        if torch.cuda.is_available():
            logger.warning("CUDA is available but will be disabled for CPU-only execution")
        
        # Set default device to CPU
        torch.set_default_device('cpu')
        
        # Disable CUDA operations
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cudnn.enabled = False
        
        # Set number of threads
        torch.set_num_threads(4)
        
        logger.info("PyTorch configured for CPU-only execution")
    except ImportError:
        logger.warning("PyTorch not installed - skipping PyTorch configuration")
    except Exception as e:
        logger.error(f"Error configuring PyTorch for CPU-only: {e}")
        raise

def configure_transformers_cpu_only() -> None:
    """
    Configure Hugging Face transformers for CPU-only execution.
    """
    try:
        from transformers import set_seed
        import transformers
      
        # Set seed for reproducibility
        set_seed(42)
        
        # Configure transformers to use CPU
        transformers.logging.set_verbosity_info()
        
        logger.info("Transformers configured for CPU-only execution")
    except ImportError:
        logger.warning("Transformers not installed - skipping transformers configuration")
    except Exception as e:
        logger.error(f"Error configuring transformers for CPU-only: {e}")
        raise

def configure_sentence_transformers_cpu_only() -> None:
    """
    Configure sentence-transformers for CPU-only execution.
    """
    try:
        import sentence_transformers
        
        # sentence-transformers uses PyTorch under the hood, so it will
        # respect the CPU configuration set earlier
        logger.info("Sentence-transformers will use CPU-only configuration from PyTorch")
    except ImportError:
        logger.warning("Sentence-transformers not installed - skipping configuration")
    except Exception as e:
        logger.error(f"Error configuring sentence-transformers for CPU-only: {e}")
        raise

def verify_cpu_constraints() -> Dict[str, Any]:
    """
    Verify that all CPU-only constraints are met.
    
    Returns:
        Dict[str, Any]: Verification results with status and details.
    """
    results = {
        'cpu_only': True,
        'environment_configured': False,
        'pytorch_configured': False,
        'transformers_configured': False,
        'sentence_transformers_configured': False,
        'details': []
    }
    
    # Set environment variables
    env_vars = set_cpu_only_environment()
    results['details'].append(f"Environment variables set: {list(env_vars.keys())}")
    
    # Validate environment
    if validate_cpu_only_environment():
        results['environment_configured'] = True
    else:
        results['cpu_only'] = False
        results['details'].append("Environment validation failed")
    
    # Configure and verify PyTorch
    try:
        import torch
        configure_pytorch_cpu_only()
        if not torch.cuda.is_available():
            results['pytorch_configured'] = True
            results['details'].append("PyTorch successfully configured for CPU-only")
        else:
            results['cpu_only'] = False
            results['details'].append("PyTorch still reports CUDA availability")
    except ImportError:
        results['details'].append("PyTorch not installed")
    except Exception as e:
        results['cpu_only'] = False
        results['details'].append(f"PyTorch configuration error: {e}")
    
    # Configure and verify transformers
    try:
        configure_transformers_cpu_only()
        results['transformers_configured'] = True
        results['details'].append("Transformers successfully configured for CPU-only")
    except ImportError:
        results['details'].append("Transformers not installed")
    except Exception as e:
        results['cpu_only'] = False
        results['details'].append(f"Transformers configuration error: {e}")
    
    # Configure and verify sentence-transformers
    try:
        configure_sentence_transformers_cpu_only()
        results['sentence_transformers_configured'] = True
        results['details'].append("Sentence-transformers successfully configured for CPU-only")
    except ImportError:
        results['details'].append("Sentence-transformers not installed")
    except Exception as e:
        results['cpu_only'] = False
        results['details'].append(f"Sentence-transformers configuration error: {e}")
    
    return results

def main() -> int:
    """
    Main entry point for CPU environment setup.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting CPU-only environment configuration...")
    
    # Set environment variables
    set_cpu_only_environment()
    
    # Validate environment
    if not validate_cpu_only_environment():
        logger.error("Environment validation failed - cannot proceed with CPU-only execution")
        return 1
    
    # Configure libraries
    try:
        configure_pytorch_cpu_only()
        configure_transformers_cpu_only()
        configure_sentence_transformers_cpu_only()
    except Exception as e:
        logger.error(f"Failed to configure libraries for CPU-only execution: {e}")
        return 1
    
    # Verify constraints
    verification = verify_cpu_constraints()
    
    if verification['cpu_only']:
        logger.info("CPU-only environment configuration completed successfully")
        logger.info(f"Verification details: {verification['details']}")
        return 0
    else:
        logger.error("CPU-only environment configuration failed")
        logger.error(f"Verification details: {verification['details']}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
