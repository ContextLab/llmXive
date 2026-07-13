from __future__ import annotations

import os
from functools import wraps
from typing import Callable, Any

def cpu_limit(max_cores: int = 4):
    """
    Decorator to limit the number of CPU cores used by a function.
    Note: This is a soft limit and depends on the underlying libraries'
    ability to respect environment variables.
    
    Args:
        max_cores: Maximum number of CPU cores to use
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Set environment variables to limit CPU usage
            os.environ["OMP_NUM_THREADS"] = str(max_cores)
            os.environ["OPENBLAS_NUM_THREADS"] = str(max_cores)
            os.environ["MKL_NUM_THREADS"] = str(max_cores)
            os.environ["VECLIB_MAXIMUM_THREADS"] = str(max_cores)
            os.environ["NUMEXPR_NUM_THREADS"] = str(max_cores)
            
            # For PyTorch
            import torch
            torch.set_num_threads(max_cores)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
