import random
import os
import numpy as np
import torch

def set_deterministic_seed(seed: int = 42) -> None:
    """
    Configure deterministic random seeds for reproducible execution.
    
    This function sets seeds for:
    - Python's built-in random module
    - NumPy
    - PyTorch (including CUDA if available)
    - Sets environment variables for deterministic behavior
    
    Args:
        seed: The random seed to use (default: 42)
    """
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy seed
    np.random.seed(seed)
    
    # Set PyTorch seeds
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    
    # Set environment variables for deterministic behavior
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Note: Full determinism in PyTorch requires additional settings
    # that may impact performance. These are commented out for efficiency:
    # torch.backends.cudnn.deterministic = True
    # torch.backends.cudnn.benchmark = False
    
    # For reproducibility in multi-threaded environments
    if torch.cuda.is_available():
        torch.use_deterministic_algorithms(True)
