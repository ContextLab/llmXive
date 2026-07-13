from __future__ import annotations

import gc
import os
from functools import wraps
from typing import Callable, Any

def memory_limit(max_bytes: int = 8 * 1024**3):
    """
    Decorator to attempt to constrain memory usage.
    Note: True memory limiting requires OS-level controls (cgroups, ulimit).
    This decorator provides soft limits via garbage collection and PyTorch
    memory management.
    
    Args:
        max_bytes: Maximum memory usage in bytes (default 8GB)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Force garbage collection before starting
            gc.collect()
            
            # Set PyTorch memory allocator parameters
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Track memory before
            try:
                import resource
                mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            except:
                mem_before = 0
            
            try:
                result = func(*args, **kwargs)
                
                # Force garbage collection after
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                return result
            finally:
                # Final cleanup
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        return wrapper
    return decorator
