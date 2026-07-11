"""
Utility functions for embedding generation pipeline.

Provides batching logic and memory safety checks.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Callable, Tuple
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug
from utils.memory_monitor import get_process_memory_mb, memory_limit_context

logger = get_logger(__name__)

def batch_process_embeddings(
    data: List[Any],
    process_func: Callable[[List[Any]], np.ndarray],
    batch_size: int = 32,
    memory_limit_mb: Optional[int] = None
) -> np.ndarray:
    """
    Process data in batches to ensure memory safety.

    Args:
        data: List of items to process (e.g., image paths, text strings).
        process_func: Function that takes a batch (list) and returns embeddings (np.ndarray).
                      Must return a 2D array of shape (batch_size, embedding_dim).
        batch_size: Number of items per batch.
        memory_limit_mb: Optional memory limit in MB. If exceeded, GC is triggered.

    Returns:
        Concatenated numpy array of all batch results with shape (total_items, embedding_dim).

    Raises:
        ValueError: If data is empty or process_func returns inconsistent shapes.
        RuntimeError: If memory limit is exceeded and cannot be recovered.
    """
    if not data:
        log_warning("Input data list is empty. Returning empty array.")
        return np.array([])

    total_items = len(data)
    results = []
    num_batches = (total_items + batch_size - 1) // batch_size

    log_info(f"Starting batch processing: {total_items} items, batch size {batch_size}, {num_batches} batches")

    for i in range(0, total_items, batch_size):
        batch = data[i : i + batch_size]
        current_batch_idx = i // batch_size + 1

        # Memory check before processing
        if memory_limit_mb:
            current_mem = get_process_memory_mb()
            if current_mem > memory_limit_mb:
                log_warning(f"Memory limit approaching ({current_mem:.1f} MB > {memory_limit_mb} MB). Triggering GC.")
                import gc
                gc.collect()
                # Check again after GC
                current_mem = get_process_memory_mb()
                if current_mem > memory_limit_mb:
                    log_error(f"Memory limit exceeded after GC ({current_mem:.1f} MB). Aborting batch {current_batch_idx}.")
                    raise RuntimeError(f"Memory limit exceeded: {current_mem:.1f} MB > {memory_limit_mb} MB")

        try:
            batch_result = process_func(batch)
            
            # Validate result
            if batch_result is None:
                log_warning(f"Batch {current_batch_idx} returned None. Skipping.")
                continue
            
            if not isinstance(batch_result, np.ndarray):
                log_error(f"Batch {current_batch_idx} returned non-numpy type: {type(batch_result)}")
                raise TypeError(f"process_func must return np.ndarray, got {type(batch_result)}")
            
            if batch_result.size == 0:
                log_warning(f"Batch {current_batch_idx} returned empty array. Skipping.")
                continue

            # Validate dimensionality (expect 2D: [batch_size, embedding_dim])
            if batch_result.ndim != 2:
                log_error(f"Batch {current_batch_idx} returned array with ndim={batch_result.ndim}, expected 2D.")
                raise ValueError(f"Expected 2D array from process_func, got {batch_result.ndim}D")

            results.append(batch_result)
            log_debug(f"Processed batch {current_batch_idx}/{num_batches}: shape {batch_result.shape}")

        except Exception as e:
            log_error(f"Failed to process batch {current_batch_idx}: {e}")
            raise

    if not results:
        log_warning("No valid results collected from any batch.")
        return np.array([])

    # Verify all batches have the same embedding dimension
    first_dim = results[0].shape[1]
    for idx, res in enumerate(results[1:], start=1):
        if res.shape[1] != first_dim:
            log_error(f"Dimension mismatch: batch 0 has dim {first_dim}, batch {idx} has dim {res.shape[1]}")
            raise ValueError(f"Inconsistent embedding dimensions: batch 0={first_dim}, batch {idx}={res.shape[1]}")

    final_array = np.vstack(results)
    log_info(f"Batch processing complete. Final shape: {final_array.shape}")
    return final_array