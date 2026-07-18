import os
import random
import numpy as np
import pytest
import torch

def pytest_configure(config):
    """
    Configure pytest to enforce random seed pinning and CPU-only execution.
    """
    # Set global random seed
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Force CPU-only for PyTorch
    if torch.cuda.is_available():
        # We explicitly set the device to CPU to avoid GPU usage
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        torch.set_num_threads(1) # Limit parallelism for reproducibility

def set_seed(seed=42):
    """
    Helper function to set seeds for reproducibility.
    Can be called in individual tests if needed.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    if torch.cuda.is_available():
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    else:
        torch.manual_seed(seed)