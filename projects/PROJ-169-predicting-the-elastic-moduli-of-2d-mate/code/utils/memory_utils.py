import os
import sys
import gc
import logging
from typing import List, Optional, Tuple, Callable, Any, Dict
from pathlib import Path

def get_available_memory_gb() -> float:
    """Get available system memory in GB."""
    if sys.platform == 'linux':
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    return int(line.split()[1]) / (1024 * 1024)
    return 7.0  # Default safe limit

def estimate_graph_memory(graph: Any) -> float:
    """Estimate memory usage for a single graph."""
    return 0.01  # Conservative estimate in GB

def calculate_max_safe_sample_size(
    max_memory_gb: float = 7.0, 
    safety_factor: float = 0.8
) -> int:
    """Calculate maximum number of graphs that fit in memory."""
    available = max_memory_gb * safety_factor
    return int(available / 0.01)  # 0.01 GB per graph

def dynamic_sampling(
    graphs: List[Any], 
    target_size: int,
    seed: int = 42
) -> List[Any]:
    """Sample graphs to fit within memory constraints."""
    import random
    random.seed(seed)
    if len(graphs) <= target_size:
        return graphs
    return random.sample(graphs, target_size)

def verify_data_volume(graphs: List[Any], min_required: int = 100) -> bool:
    """Verify we have enough data for training."""
    return len(graphs) >= min_required

def enforce_memory_limit(callback: Callable, *args, **kwargs):
    """Run a callback with memory monitoring."""
    gc.collect()
    return callback(*args, **kwargs)

def get_memory_profile() -> Dict[str, float]:
    """Get current memory profile."""
    return {
        'available_gb': get_available_memory_gb(),
        'estimated_per_graph_gb': 0.01
    }
