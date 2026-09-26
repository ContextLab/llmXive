import pytest
import os
import gc
import sys
import tracemalloc
from pathlib import Path
from typing import Generator, Dict, Any
from itertools import islice

# Add code to path if not already there
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from lib.data_loader import (
    profile_memory_usage, 
    get_current_memory_gb, 
    load_ruler_dataset_streaming,
    MemoryLimitedLoader
)

def generate_synthetic_moderate_stream(num_items: int = 5000, item_size_kb: int = 10) -> Generator[Dict[str, Any], None, None]:
    """
    Generates a synthetic moderate-sized stream for testing memory limits.
    Simulates data chunks of roughly 10KB each.
    Total size approx: 5000 * 10KB = 50MB, well under 7GB limit.
    """
    data_block = "x" * (item_size_kb * 1024)
    for i in range(num_items):
        yield {
            "id": i,
            "content": data_block,
            "metadata": {"index": i, "source": "synthetic_test"}
        }
        # Force garbage collection occasionally to ensure accurate measurement
        if i % 500 == 0:
            gc.collect()

def test_peak_memory():
    """
    Unit test asserting peak memory usage < 7GB on a 100-document sample 
    from the RULER validation split.
    
    This test:
    1. Loads exactly 100 documents from the real RULER validation split.
    2. Profiles memory usage during iteration.
    3. Asserts peak memory remains under 7GB.
    """
    limit_gb = 7.0
    log_path = "data/logs/memory_profile.csv"
    
    # Ensure data/logs directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Reset garbage collector to ensure clean state
    gc.collect()
    
    # Remove old log if exists to start fresh
    if os.path.exists(log_path):
        os.remove(log_path)
    
    try:
        # Start tracing
        tracemalloc.start()
        
        # Load exactly 100 documents from RULER validation split
        stream = load_ruler_dataset_streaming(
            split="validation",
            streaming=True,
            sample_size=100
        )
        
        # Wrap with memory profiler
        profiled_stream = profile_memory_usage(stream, limit_gb=limit_gb, log_path=log_path)
        
        # Consume the stream
        count = 0
        for item in profiled_stream:
            count += 1
            if count % 20 == 0:
                gc.collect()
        
        # Verify we processed exactly 100 items
        assert count == 100, f"Expected 100 items, got {count}"
        
        # Verify the log file was created
        assert os.path.exists(log_path), f"Memory profile log not created at {log_path}"
        
        # Read the log to verify peak memory
        peak_memory = 0.0
        with open(log_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                mem = float(row['memory_gb'])
                if mem > peak_memory:
                    peak_memory = mem
        
        # Assert peak memory is strictly less than the limit
        assert peak_memory < limit_gb, f"Peak memory {peak_memory:.2f}GB exceeded limit {limit_gb}GB"
        
        logger = __import__('logging').getLogger(__name__)
        logger.info(f"Test passed. Peak memory: {peak_memory:.4f}GB")
        
    except MemoryError as e:
        pytest.fail(f"Memory limit was incorrectly triggered: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during test: {e}")
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        gc.collect()

def test_memory_enforcement():
    """
    Test that MemoryError is raised when memory limit is exceeded.
    Uses a synthetic stream that simulates high memory usage.
    """
    limit_gb = 0.001  # Very low limit to force error
    log_path = "data/logs/memory_test_enforcement.csv"
    
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    if os.path.exists(log_path):
        os.remove(log_path)
    
    # Create a stream that simulates large items
    def large_stream():
        large_data = "x" * (1024 * 1024 * 100)  # 100MB item
        for i in range(5):
            yield {"id": i, "content": large_data}
    
    stream = large_stream()
    profiled_stream = profile_memory_usage(stream, limit_gb=limit_gb, log_path=log_path)
    
    with pytest.raises(MemoryError):
        for _ in profiled_stream:
            pass