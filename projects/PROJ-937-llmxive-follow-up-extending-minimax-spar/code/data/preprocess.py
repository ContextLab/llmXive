"""
Preprocessing utilities for the llmXive pipeline.
Handles context chunking, memory monitoring, and batch reduction strategies.
"""
import os
import sys
import gc
import logging
import resource
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass, field

# Local imports based on project API surface
from utils.logger import get_logger_for_task, log_resource_usage

logger = get_logger_for_task("T007d")

@dataclass
class PreprocessConfig:
    """Configuration for preprocessing operations."""
    max_context_tokens: int = 4096
    initial_batch_size: int = 32
    min_batch_size: int = 1
    memory_threshold_gb: float = 6.5
    reduction_factor: float = 0.5

def get_available_memory_gb() -> float:
    """
    Returns the available system memory in GB.
    Uses resource module for POSIX or psutil if available (fallback to resource).
    """
    try:
        # Try psutil first if available (often used in T040)
        import psutil
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    except ImportError:
        # Fallback to resource module (POSIX)
        try:
            # Get soft limit; if unlimited, estimate based on system
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            if soft == resource.RLIM_INFINITY:
                # Estimate from total memory if limit is unlimited
                total_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 # MB
                return max(1.0, total_mem * 0.8) # Heuristic
            return soft / (1024 ** 3)
        except Exception:
            logger.warning("Could not determine available memory via resource module. Returning 1.0 GB default.")
            return 1.0

def get_used_memory_gb() -> float:
    """
    Returns the currently used memory by the process in GB.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    except ImportError:
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, MB on macOS
            # Normalize to GB
            if sys.platform == 'darwin':
                return usage.ru_maxrss / (1024 ** 2)
            else:
                return usage.ru_maxrss / (1024 ** 3)
        except Exception:
            logger.warning("Could not determine used memory. Returning 0.0 GB default.")
            return 0.0

def check_memory_usage() -> bool:
    """
    Checks if current memory usage exceeds the configured threshold (6.5 GB).
    Returns True if usage > 6.5 GB (memory pressure detected).
    """
    used_gb = get_used_memory_gb()
    threshold = 6.5
    is_over = used_gb > threshold
    if is_over:
        logger.warning(f"Memory usage ({used_gb:.2f} GB) exceeds threshold ({threshold} GB).")
    else:
        logger.debug(f"Memory usage ({used_gb:.2f} GB) is within threshold ({threshold} GB).")
    return is_over

def reduce_context_window(config: PreprocessConfig) -> bool:
    """
    Attempts to reduce the context window size to alleviate memory pressure.
    Returns True if reduction was successful and new size > 0.
    """
    if config.max_context_tokens <= 0:
        return False
    
    new_size = max(1, int(config.max_context_tokens * config.reduction_factor))
    if new_size < config.max_context_tokens:
        old_size = config.max_context_tokens
        config.max_context_tokens = new_size
        logger.info(f"Reduced context window from {old_size} to {new_size} tokens.")
        gc.collect()
        return True
    return False

def reduce_batch_size(batch_size: int) -> int:
    """
    Reduces the batch size by half.
    Returns the new batch size.
    """
    if batch_size <= 1:
        return 1
    new_size = max(1, batch_size // 2)
    if new_size < batch_size:
        logger.info(f"Reduced batch size from {batch_size} to {new_size}.")
        gc.collect()
    return new_size

def exit_on_memory_exceeded(config: PreprocessConfig, current_batch_size: int) -> None:
    """
    Checks if memory is exceeded. If so, attempts to reduce context window
    and then batch size. If both reduction modes fail (context cannot be reduced
    further or batch size is already at minimum), raises a RuntimeError.
    
    This function implements the exit logic for T007d.
    
    Args:
        config: The PreprocessConfig object to modify.
        current_batch_size: The current batch size being used.
        
    Raises:
        RuntimeError: If memory constraints cannot be resolved by reduction.
    """
    if not check_memory_usage():
        return

    logger.error("Memory constraint exceeded. Attempting recovery strategies...")

    # Strategy 1: Reduce Context Window
    context_reduced = reduce_context_window(config)
    
    # Check memory again after context reduction
    if not check_memory_usage():
        logger.info("Context reduction resolved memory pressure.")
        return

    # Strategy 2: Reduce Batch Size
    new_batch_size = reduce_batch_size(current_batch_size)
    if new_batch_size < current_batch_size:
        # Check memory again after batch reduction
        if not check_memory_usage():
            logger.info("Batch size reduction resolved memory pressure.")
            return
    
    # If we are here, both strategies failed to resolve the issue
    # or we couldn't reduce further (e.g., batch size already 1, context already min)
    logger.critical("All memory reduction strategies failed. Exiting.")
    raise RuntimeError("Memory constraint exceeded")

def split_context(context: str, chunk_size: int) -> Generator[str, None, None]:
    """
    Splits a long context string into chunks of approximately chunk_size.
    Yields chunks of text.
    
    Args:
        context: The input text string.
        chunk_size: The approximate number of tokens/characters per chunk.
        
    Yields:
        String chunks.
    """
    if not context:
        return
    
    # Simple character-based splitting for now, could be token-based if tokenizer available
    # Assuming chunk_size refers to characters for this generic utility unless specified
    # If token-based logic is required, it should use a specific tokenizer.
    # For this task, we implement a robust string splitter.
    
    start = 0
    while start < len(context):
        end = start + chunk_size
        yield context[start:end]
        start = end

def main():
    """
    Main entry point for testing the preprocessing logic.
    """
    logging.basicConfig(level=logging.INFO)
    config = PreprocessConfig()
    
    # Simulate a scenario where memory is high
    # In a real scenario, this would be triggered by actual load
    logger.info("Testing memory reduction logic...")
    
    # This is a unit test simulation; in real execution, 
    # exit_on_memory_exceeded would be called within the data loading loop.
    try:
        # Force a memory check (will likely pass on a clean run)
        # To test the failure path, one would need to artificially inflate memory
        # or run on a constrained machine.
        # We demonstrate the call signature here.
        exit_on_memory_exceeded(config, 32)
        logger.info("Memory check passed or reduced successfully.")
    except RuntimeError as e:
        logger.error(f"Memory constraint error caught: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()