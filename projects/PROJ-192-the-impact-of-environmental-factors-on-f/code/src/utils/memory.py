import logging
from typing import Optional
import psutil

logger = logging.getLogger(__name__)

_subsampling_active = False
_subsample_ratio = 1.0
_subsample_indices = None

def get_memory_status() -> float:
    """
    Get current memory usage in GB.
    
    Returns:
        Current memory usage in GB.
    """
    process = psutil.Process()
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)  # Convert to GB

def trigger_subsample(current_ram: float, max_ram: float) -> bool:
    """
    Trigger subsampling logic when memory exceeds threshold.
    
    Args:
        current_ram: Current memory usage in GB.
        max_ram: Maximum allowed memory in GB.
        
    Returns:
        True if subsampling was triggered.
    """
    global _subsampling_active, _subsample_ratio
    
    if current_ram > max_ram:
        ratio = max_ram / current_ram
        _subsampling_active = True
        _subsample_ratio = ratio
        logger.warning(f"Memory usage ({current_ram:.2f} GB) exceeds limit ({max_ram} GB). "
                       f"Subsampling ratio: {ratio:.2f}")
        return True
    return False

def is_subsampling_active() -> bool:
    """
    Check if subsampling is currently active.
    
    Returns:
        True if subsampling is active.
    """
    return _subsampling_active

def get_subsample_ratio() -> float:
    """
    Get the current subsampling ratio.
    
    Returns:
        Subsampling ratio (0.0 to 1.0).
    """
    return _subsample_ratio

def get_subsample_indices(n: int) -> list:
    """
    Get indices for subsampling a dataset of size n.
    
    Args:
        n: Total number of items.
        
    Returns:
        List of indices to keep.
    """
    global _subsample_indices
    
    if _subsample_indices is None:
        ratio = get_subsample_ratio()
        num_keep = int(n * ratio)
        # Simple approach: keep first num_keep items
        # In a real scenario, we might use random sampling
        _subsample_indices = list(range(num_keep))
    
    return _subsample_indices