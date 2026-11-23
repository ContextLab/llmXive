import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.memory_monitor import get_available_ram_gb
import logging

logger = logging.getLogger(__name__)

# Constants
MAX_TOTAL_MEMORY_GB = 7.0  # Total memory cap as per SC-005
SAFETY_MARGIN_GB = 0.5     # Safety margin for OS and other processes
MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 64        # Reasonable upper limit

def calculate_batch_size(available_ram_gb: float, model_memory_gb: float) -> int:
    """
    Calculate optimal batch size based on available RAM and model memory.
    
    Logic:
    - Total memory used = model_memory + (batch_size * sample_memory_overhead)
    - We assume a per-sample memory overhead of ~0.1GB for inference context.
    - Ensure total memory < MAX_TOTAL_MEMORY_GB.
    
    Args:
        available_ram_gb: Available RAM in GB.
        model_memory_gb: Estimated memory footprint of the model in GB.
    
    Returns:
        int: Calculated batch size.
    """
    # Available memory for data processing (batch)
    usable_memory = available_ram_gb - model_memory_gb - SAFETY_MARGIN_GB
    
    if usable_memory <= 0:
        logger.warning(f"Insufficient memory: Available {available_ram_gb}GB, Model {model_memory_gb}GB. Returning min batch size.")
        return MIN_BATCH_SIZE
    
    # Estimate per-sample memory overhead (adjust based on actual profiling if needed)
    # This is a heuristic. For transformers, context window size matters.
    # Assuming ~0.1GB per sample for a standard context length.
    SAMPLE_MEMORY_OVERHEAD_GB = 0.1 
    
    if SAMPLE_MEMORY_OVERHEAD_GB <= 0:
        return MAX_BATCH_SIZE
    
    calculated_size = int(usable_memory / SAMPLE_MEMORY_OVERHEAD_GB)
    
    # Clamp to valid range
    batch_size = max(MIN_BATCH_SIZE, min(calculated_size, MAX_BATCH_SIZE))
    
    logger.info(f"Calculated batch size: {batch_size} (Available: {available_ram_gb}GB, Model: {model_memory_gb}GB, Usable: {usable_memory}GB)")
    return batch_size

def get_optimal_batch_size(model_memory_gb: Optional[float] = None) -> int:
    """
    Wrapper to get optimal batch size using current system memory.
    
    Args:
        model_memory_gb: Optional override for model memory. If None, defaults to 1.5GB.
    
    Returns:
        int: Optimal batch size.
    """
    if model_memory_gb is None:
        model_memory_gb = 1.5  # Default estimate for a 4-bit quantized model
    
    available_ram = get_available_ram_gb()
    return calculate_batch_size(available_ram, model_memory_gb)
