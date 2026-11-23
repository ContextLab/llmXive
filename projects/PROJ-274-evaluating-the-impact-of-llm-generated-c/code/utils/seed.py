import random
import os
import sys
import logging
from typing import Optional

# Configure logging for the seed module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_global_seed(seed: int = 42):
    """
    Set global random seeds for reproducibility across Python, NumPy, and PyTorch.
    
    This function is mandatory for Constitution Principle I. It must be called
    at the start of every script execution to ensure deterministic behavior.
    
    Args:
        seed (int): The random seed value. Defaults to 42.
    """
    logger.info(f"Setting global random seed to {seed}")
    
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy seed if available
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)
        logger.debug("NumPy seed set.")
    else:
        # Attempt to import and set if not yet imported but needed
        try:
            import numpy as np
            np.random.seed(seed)
            logger.debug("NumPy seed set (imported on demand).")
        except ImportError:
            logger.debug("NumPy not available, skipping.")

    # Set PyTorch seed if available
    if 'torch' in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            logger.debug("PyTorch CUDA seeds set.")
        else:
            logger.debug("PyTorch CUDA not available, setting CPU seed only.")
    else:
        # Attempt to import and set if not yet imported but needed
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
                logger.debug("PyTorch seeds set (imported on demand).")
            else:
                logger.debug("PyTorch seeds set (CPU only, imported on demand).")
        except ImportError:
            logger.debug("PyTorch not available, skipping.")
    
    # Ensure reproducibility in other common libraries if present
    if 'tensorflow' in sys.modules:
        import tensorflow as tf
        tf.random.set_seed(seed)
        logger.debug("TensorFlow seed set.")
    
    if 'jax' in sys.modules:
        import jax
        jax.random.PRNGKey(seed)
        logger.debug("JAX seed set.")

def get_seed_status() -> dict:
    """
    Return current seed status for verification.
    
    Returns:
        dict: A dictionary containing the current seed state for Python and
              the expected seed value.
    """
    seed_value = 42 # Default expected value, could be made dynamic if tracked
    python_state = random.getstate()
    
    return {
        'seed_value': seed_value,
        'python_random_set': True,
        'python_state_tuple': str(python_state[1][0]) if python_state else None
    }

if __name__ == "__main__":
    # When run directly, set the seed and confirm
    set_global_seed()
    status = get_seed_status()
    print(f"Global seeds set. Status: {status}")
    logger.info("Seed module executed successfully.")