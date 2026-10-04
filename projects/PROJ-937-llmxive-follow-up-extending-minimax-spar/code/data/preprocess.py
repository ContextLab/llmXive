import os
import sys
import gc
import logging
import resource
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Generator
from dataclasses import dataclass, field
import psutil

from utils.config import Config
from utils.logger import get_logger_for_task

# Configure logger
logger = get_logger_for_task("T007d")

@dataclass
class PreprocessConfig:
    """Configuration for preprocessing memory checks and reductions."""
    memory_threshold_gb: float = 6.5
    max_reduction_attempts: int = 3
    min_batch_size: int = 1
    chunk_size: int = 512
    context_reduction_factor: float = 0.5

def get_available_memory_gb() -> float:
    """Get available system memory in GB."""
    if sys.platform == "win32":
        # Windows specific
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    else:
        # Unix-like systems
        try:
            # Try to get available memory from /proc/meminfo if available
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('MemAvailable:'):
                        return float(line.split()[1]) / (1024 * 1024)  # Convert KB to GB
        except (FileNotFoundError, IndexError, ValueError):
            pass
        
        # Fallback to psutil
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)

def get_used_memory_gb() -> float:
    """Get currently used system memory in GB."""
    mem = psutil.virtual_memory()
    return mem.used / (1024 ** 3)

def check_memory_usage() -> bool:
    """
    Check if current memory usage exceeds the threshold.
    
    Returns:
        True if memory usage > threshold, False otherwise.
    """
    used_gb = get_used_memory_gb()
    config = PreprocessConfig()
    if used_gb > config.memory_threshold_gb:
        logger.warning(
            f"Memory usage {used_gb:.2f}GB exceeds threshold {config.memory_threshold_gb}GB"
        )
        return True
    return False

def split_context(context: str, chunk_size: int = 512) -> Generator[str, None, None]:
    """
    Split a context string into chunks of specified size.
    
    Args:
        context: The input context string.
        chunk_size: Maximum size of each chunk.
        
    Yields:
        Chunks of the context string.
    """
    if not context:
        return
    
    start = 0
    while start < len(context):
        end = min(start + chunk_size, len(context))
        yield context[start:end]
        start = end

def reduce_batch_size(batch: List[Any], target_size: Optional[int] = None) -> List[Any]:
    """
    Reduce batch size if memory pressure is detected.
    
    Args:
        batch: The input batch list.
        target_size: Optional target batch size. If None, reduces by half.
        
    Returns:
        Reduced batch list.
    """
    if not batch:
        return batch
    
    config = PreprocessConfig()
    current_size = len(batch)
    
    if target_size is None:
        target_size = max(config.min_batch_size, current_size // 2)
    
    target_size = max(config.min_batch_size, min(target_size, current_size))
    
    if target_size < current_size:
        logger.info(f"Reducing batch size from {current_size} to {target_size}")
        return batch[:target_size]
    
    return batch

def reduce_context_window(context: str, factor: float = 0.5) -> str:
    """
    Reduce context window size by a given factor.
    
    Args:
        context: The input context string.
        factor: Reduction factor (0.0 to 1.0). 0.5 means keep first 50%.
        
    Returns:
        Reduced context string.
    """
    config = PreprocessConfig()
    if factor <= 0.0 or factor > 1.0:
        factor = config.context_reduction_factor
    
    new_length = int(len(context) * factor)
    if new_length == 0:
        new_length = 1
    
    logger.info(f"Reducing context window from {len(context)} to {new_length} tokens")
    return context[:new_length]

def exit_on_memory_exceeded() -> None:
    """
    Raise RuntimeError if all memory reduction strategies have been exhausted.
    
    This function is called after attempting to reduce batch size and context window.
    If memory pressure persists after all reduction attempts, it raises a RuntimeError
    to prevent OOM crashes and signal that the task cannot proceed within constraints.
    
    Raises:
        RuntimeError: Always raised with message "Memory constraint exceeded"
    """
    config = PreprocessConfig()
    used_gb = get_used_memory_gb()
    available_gb = get_available_memory_gb()
    
    logger.critical(
        f"Memory constraint exceeded: Used {used_gb:.2f}GB, Available {available_gb:.2f}GB, "
        f"Threshold {config.memory_threshold_gb}GB"
    )
    logger.critical(
        "All reduction strategies (batch size reduction, context window reduction) have been exhausted. "
        "Cannot proceed within memory constraints."
    )
    
    raise RuntimeError("Memory constraint exceeded")

def main() -> None:
    """
    Main function to demonstrate memory checking and reduction logic.
    This is primarily for testing and validation of the memory guard mechanisms.
    """
    logger.info("Starting memory check demonstration")
    
    # Test memory checking
    logger.info(f"Current memory usage: {get_used_memory_gb():.2f}GB")
    logger.info(f"Available memory: {get_available_memory_gb():.2f}GB")
    
    if check_memory_usage():
        logger.warning("Memory pressure detected, attempting reductions...")
        
        # Simulate batch reduction
        test_batch = list(range(1000))
        reduced_batch = reduce_batch_size(test_batch)
        logger.info(f"Batch reduced from {len(test_batch)} to {len(reduced_batch)}")
        
        # Simulate context reduction
        test_context = "A" * 10000
        reduced_context = reduce_context_window(test_context)
        logger.info(f"Context reduced from {len(test_context)} to {len(reduced_context)}")
        
        # If still over threshold, exit
        if check_memory_usage():
            logger.error("Memory still exceeded after reductions, exiting...")
            exit_on_memory_exceeded()
    else:
        logger.info("Memory usage within acceptable limits")
    
    logger.info("Memory check demonstration completed successfully")

if __name__ == "__main__":
    main()