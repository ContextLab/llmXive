import os
import sys
import gc
import logging
import tracemalloc
from typing import List, Optional, Tuple, Callable, Any, Dict
from pathlib import Path

# Constants for memory limits
MAX_MEMORY_GB = 7.0
SAFETY_FACTOR = 0.8
ESTIMATED_GRAPH_SIZE_GB = 0.01  # Conservative estimate per graph

logger = logging.getLogger(__name__)

def get_available_memory_gb() -> float:
    """Get available system memory in GB.
    
    Reads /proc/meminfo on Linux, returns default safe limit on other platforms.
    """
    if sys.platform == 'linux':
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        # Value is in kB
                        return int(line.split()[1]) / (1024 * 1024)
        except (IOError, ValueError, IndexError) as e:
            logger.warning(f"Could not read memory info: {e}. Using default.")
    return MAX_MEMORY_GB

def estimate_graph_memory(graph: Any) -> float:
    """Estimate memory usage for a single graph in GB.
    
    Args:
        graph: A graph object (e.g., torch_geometric.data.Data or dict)
    
    Returns:
        Estimated memory usage in GB (conservative constant for now)
    """
    # For now, use a conservative constant.
    # In a more advanced implementation, we could inspect graph.node_features,
    # graph.edge_index, etc., to calculate a more precise size.
    return ESTIMATED_GRAPH_SIZE_GB

def calculate_max_safe_sample_size(
    max_memory_gb: float = MAX_MEMORY_GB, 
    safety_factor: float = SAFETY_FACTOR
) -> int:
    """Calculate maximum number of graphs that fit in memory.
    
    Args:
        max_memory_gb: Total memory limit in GB
        safety_factor: Fraction of memory to use for safety margin
    
    Returns:
        Maximum number of graphs that can be safely loaded
    """
    available = max_memory_gb * safety_factor
    # Ensure we don't divide by zero if estimate changes
    if ESTIMATED_GRAPH_SIZE_GB <= 0:
        raise ValueError("ESTIMATED_GRAPH_SIZE_GB must be positive")
    return int(available / ESTIMATED_GRAPH_SIZE_GB)

def dynamic_sampling(
    graphs: List[Any], 
    target_size: int,
    seed: int = 42
) -> List[Any]:
    """Sample graphs to fit within memory constraints.
    
    If the input list is larger than target_size, randomly samples down.
    Otherwise, returns the original list.
    
    Args:
        graphs: List of graph objects
        target_size: Maximum number of graphs to keep
        seed: Random seed for reproducibility
    
    Returns:
        A list of graphs with size <= target_size
    """
    import random
    random.seed(seed)
    if len(graphs) <= target_size:
        return graphs
    return random.sample(graphs, target_size)

def verify_data_volume(graphs: List[Any], min_required: int = 100) -> bool:
    """Verify we have enough data for training.
    
    Args:
        graphs: List of graph objects
        min_required: Minimum number of graphs required
    
    Returns:
        True if len(graphs) >= min_required, False otherwise
    """
    return len(graphs) >= min_required

def enforce_memory_limit(
    callback: Callable, 
    *args, 
    peak_memory_callback: Optional[Callable[[float], None]] = None,
    **kwargs
) -> Any:
    """Run a callback with memory monitoring and enforcement.
    
    Starts tracing memory, runs the callback, and checks if peak usage
    exceeds the limit. If it does, raises a MemoryError.
    
    Args:
        callback: The function to execute
        *args: Arguments to pass to callback
        peak_memory_callback: Optional callback to receive peak memory usage
        **kwargs: Keyword arguments to pass to callback
    
    Returns:
        The return value of the callback
    
    Raises:
        MemoryError: If peak memory usage exceeds MAX_MEMORY_GB
    """
    gc.collect()
    tracemalloc.start()
    
    try:
        result = callback(*args, **kwargs)
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_gb = peak / (1024 * 1024 * 1024)
        
        if peak_memory_callback:
            peak_memory_callback(peak_gb)
        
        if peak_gb > MAX_MEMORY_GB:
            logger.error(f"Memory limit exceeded: {peak_gb:.2f}GB > {MAX_MEMORY_GB}GB")
            raise MemoryError(f"Peak memory usage {peak_gb:.2f}GB exceeded limit of {MAX_MEMORY_GB}GB")
        
        logger.info(f"Peak memory usage: {peak_gb:.2f}GB (limit: {MAX_MEMORY_GB}GB)")
    
    return result

def get_memory_profile() -> Dict[str, float]:
    """Get current memory profile.
    
    Returns:
        Dictionary with available memory and estimated per-graph memory
    """
    return {
        'available_gb': get_available_memory_gb(),
        'estimated_per_graph_gb': ESTIMATED_GRAPH_SIZE_GB,
        'max_safe_sample_size': calculate_max_safe_sample_size()
    }
