import os
import gc
import sys
import time
import psutil
from typing import Generator, Dict, Any, List, Optional, Callable, Tuple

# Constants
MEMORY_TRIGGER_GB = 6.5
MEMORY_TRIGGER_BYTES = MEMORY_TRIGGER_GB * 1024**3

def get_current_memory_usage_bytes() -> int:
    """
    Returns the current memory usage of the Python process in bytes.
    Uses psutil for cross-platform compatibility.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss  # Resident Set Size

def should_trigger_batch_processing(current_memory_bytes: int, threshold_bytes: int) -> bool:
    """
    Determines if the current memory usage exceeds the threshold.
    """
    return current_memory_bytes >= threshold_bytes

def trigger_memory_cleanup() -> None:
    """
    Forces garbage collection to free up memory.
    """
    gc.collect()
    # Optional: Clear CUDA cache if GPU is used (though task specifies CPU)
    # import torch
    # if torch.cuda.is_available():
    #     torch.cuda.empty_cache()
    print("Memory cleanup triggered.")

def process_batch_with_memory_check(
    batch: List[Dict[str, Any]],
    processor_fn: Callable[[Dict[str, Any]], Any],
    memory_threshold_bytes: int = MEMORY_TRIGGER_BYTES,
) -> List[Any]:
    """
    Processes a batch of items. Before processing, checks memory usage.
    If memory is high, triggers cleanup.
    Returns a list of results.
    """
    current_memory = get_current_memory_usage_bytes()
    
    if should_trigger_batch_processing(current_memory, memory_threshold_bytes):
        print(f"Memory usage {current_memory / 1024**3:.2f} GB exceeds threshold. Cleaning up...")
        trigger_memory_cleanup()
        # Re-check memory after cleanup
        current_memory = get_current_memory_usage_bytes()
        if should_trigger_batch_processing(current_memory, memory_threshold_bytes):
            raise MemoryError(f"Memory usage still high after cleanup: {current_memory / 1024**3:.2f} GB")

    results = []
    for item in batch:
        try:
            result = processor_fn(item)
            results.append(result)
        except Exception as e:
            print(f"Error processing item in batch: {e}")
            # Decide whether to fail fast or continue. 
            # For robustness, we continue but log.
            results.append({'error': str(e), 'item_id': item.get('id', 'unknown')})
    
    return results

def adaptive_batch_size_processor(
    data_generator: Generator[Dict[str, Any], None, None],
    processor_fn: Callable[[Dict[str, Any]], Any],
    initial_batch_size: int = 10,
    memory_threshold_bytes: int = MEMORY_TRIGGER_BYTES,
) -> Generator[Any, None, None]:
    """
    Processes data from a generator with adaptive batch sizing.
    If memory usage is high, it reduces batch size or processes item-by-item.
    """
    batch = []
    batch_size = initial_batch_size
    
    for item in data_generator:
        batch.append(item)
        
        if len(batch) >= batch_size:
            # Check memory
            current_memory = get_current_memory_usage_bytes()
            if should_trigger_batch_processing(current_memory, memory_threshold_bytes):
                # If memory is high, try to process a smaller batch or single items
                # For simplicity, we process the current batch and then reduce batch size
                if len(batch) > 1:
                    print(f"High memory detected. Processing batch of size {len(batch)} and reducing batch size.")
                    batch_size = max(1, batch_size // 2)
                
                results = process_batch_with_memory_check(batch, processor_fn, memory_threshold_bytes)
                for r in results:
                    yield r
                batch = []
            else:
                results = process_batch_with_memory_check(batch, processor_fn, memory_threshold_bytes)
                for r in results:
                    yield r
                batch = []
    
    # Process remaining
    if batch:
        results = process_batch_with_memory_check(batch, processor_fn, memory_threshold_bytes)
        for r in results:
            yield r

def main():
    """
    Example usage for testing the streaming module.
    """
    print("Streaming module loaded successfully.")
    print(f"Memory trigger set to {MEMORY_TRIGGER_GB} GB ({MEMORY_TRIGGER_BYTES} bytes)")
    
    # Simple test
    current_mem = get_current_memory_usage_bytes()
    print(f"Current memory: {current_mem / 1024**3:.2f} GB")
    
    if should_trigger_batch_processing(current_mem, MEMORY_TRIGGER_BYTES):
        print("Memory trigger condition met immediately (unlikely on fresh start).")
    else:
        print("Memory usage is within limits.")

if __name__ == "__main__":
    main()