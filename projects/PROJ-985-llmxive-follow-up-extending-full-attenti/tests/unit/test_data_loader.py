import pytest
import os
import gc
import sys
import tracemalloc
from pathlib import Path
from typing import Generator, Dict, Any

# Add code to path if not already there
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from lib.data_loader import profile_memory_usage, get_current_memory_gb

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

def test_peak_memory_usage_under_limit():
    """
    Unit test asserting peak memory usage < 7GB on a synthetic Moderate-sized stream.
    This test verifies that the memory profiling logic works and that the stream
    does not exceed the defined limit.
    """
    limit_gb = 7.0
    log_path = "data/logs/memory_profile.csv"
    
    # Ensure data/logs directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Reset garbage collector to ensure clean state
    gc.collect()
    
    try:
        # Start the profiled generator
        stream = generate_synthetic_moderate_stream(num_items=5000, item_size_kb=10)
        profiled_stream = profile_memory_usage(stream, limit_gb=limit_gb, log_path=log_path)
        
        # Consume the entire stream
        count = 0
        for item in profiled_stream:
            count += 1
            if count % 1000 == 0:
                gc.collect()
        
        # Verify we processed the expected number of items
        assert count == 5000, f"Expected 5000 items, got {count}"
        
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
        
        # Assert peak memory is well below the limit (allowing a small buffer for overhead)
        # The synthetic data is small (~50MB), so peak should be very low.
        # We assert it is strictly less than the limit.
        assert peak_memory < limit_gb, f"Peak memory {peak_memory:.2f}GB exceeded limit {limit_gb}GB"
        assert peak_memory < 1.0, f"Peak memory {peak_memory:.2f}GB is unexpectedly high for synthetic test (expected < 1GB)"
        
        logger = __import__('logging').getLogger(__name__)
        logger.info(f"Test passed. Peak memory: {peak_memory:.4f}GB")
        
    except MemoryError as e:
        pytest.fail(f"Memory limit was incorrectly triggered: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during test: {e}")