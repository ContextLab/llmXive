"""
Unit tests for streaming/chunking memory constraints.

Task: T011c
Story: US1 - Data Aggregation and Preprocessing Pipeline
"""
import tracemalloc
import gc
import pytest
from typing import Generator, Dict, Any, List
import json
import tempfile
from pathlib import Path

# Constants for memory limits (in bytes)
MEMORY_LIMIT_MB = 500
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_MB * 1024 * 1024

# Constants for mock data generation
ROW_SIZE_ESTIMATE_BYTES = 2048  # Approximate size of a row in memory
CHUNK_SIZE = 1000  # Number of rows per chunk


def generate_large_stream_mock(n_rows: int) -> Generator[Dict[str, Any], None, None]:
    """
    Simulates a large data stream by yielding rows one by one (or in small batches)
    without loading the entire dataset into memory at once.
    
    This mimics the behavior of a real streaming fetcher (e.g., from an API or file).
    
    Args:
        n_rows: Total number of rows to simulate.
        
    Yields:
        Dictionary representing a single row of data.
    """
    # Pre-allocate a template row to ensure consistent structure
    template_row = {
        "experiment_id": "EXP-000000",
        "source_name": "Mock Source",
        "source_id": "SID-000000",
        "material_type": "Ceramic",
        "milling_speed": 500.0,
        "milling_time": 60.0,
        "ball_to_powder_ratio": 10.0,
        "youngs_modulus": 300.0,
        "density": 5.5,
        "d10": 10.0,
        "d50": 50.0,
        "d90": 100.0,
        "process_duration": 3600.0
    }
    
    for i in range(n_rows):
        # Update IDs to make them unique
        row = template_row.copy()
        row["experiment_id"] = f"EXP-{i:06d}"
        row["source_id"] = f"SID-{i:06d}"
        
        # Yield the row immediately to simulate streaming
        yield row
        
        # Force garbage collection periodically to keep memory profile clean
        # This simulates the real-world behavior where processed chunks are discarded
        if i % (CHUNK_SIZE * 10) == 0:
            gc.collect()


def test_streaming_memory_limit():
    """
    Test that iterating a large dataset stream does not exceed the memory limit.
    
    Action:
        1. Start tracemalloc.
        2. Iterate a mock generator yielding a substantial dataset (simulating large stream).
        3. Profile memory usage during iteration.
        4. Assert that current memory usage never exceeds 500MB.
        
    Verification:
        Assert `tracemalloc.get_traced_memory()[0]` (current memory) never exceeds 500MB.
    """
    # Define the number of rows to simulate.
    # With ROW_SIZE_ESTIMATE_BYTES ~ 2KB, 100k rows ~ 200MB base.
    # We add overhead to ensure we stress the limit without hitting it if streaming works.
    # If the code loads everything into a list, this would easily exceed 500MB.
    N_ROWS = 150_000 
    
    # Start memory tracing
    tracemalloc.start()
    
    try:
        # Create the generator
        stream = generate_large_stream_mock(N_ROWS)
        
        # Variables to track peak memory
        max_memory_observed = 0
        
        # Iterate through the stream
        # We do NOT accumulate the data into a list (which would cause O(N) memory)
        # Instead, we process and discard (simulating writing to disk or online stats)
        count = 0
        for row in stream:
            # Simulate processing (e.g., validation, transformation)
            # In a real scenario, this might write to a file or update online stats
            _ = row["experiment_id"]  # Access a field
            
            count += 1
            
            # Check memory periodically to catch spikes
            if count % CHUNK_SIZE == 0:
                current, peak = tracemalloc.get_traced_memory()
                if current > max_memory_observed:
                    max_memory_observed = current
                
                # Optional: Force GC to ensure we are measuring the streaming overhead,
                # not accumulation of unreferenced objects
                gc.collect()
                
                # Early exit if we already exceeded the limit (fail fast)
                if current > MEMORY_LIMIT_BYTES:
                    pytest.fail(
                        f"Memory limit exceeded during streaming. "
                        f"Current memory: {current / (1024*1024):.2f} MB. "
                        f"Limit: {MEMORY_LIMIT_MB} MB. "
                        f"Rows processed: {count}"
                    )
        
        # Final check
        current, peak = tracemalloc.get_traced_memory()
        if current > MEMORY_LIMIT_BYTES:
            pytest.fail(
                f"Memory limit exceeded at end of stream. "
                f"Current memory: {current / (1024*1024):.2f} MB. "
                f"Limit: {MEMORY_LIMIT_MB} MB."
            )
        
        # Assert the limit was respected throughout
        assert max_memory_observed <= MEMORY_LIMIT_BYTES, (
            f"Streaming memory exceeded limit. "
            f"Max observed: {max_memory_observed / (1024*1024):.2f} MB, "
            f"Limit: {MEMORY_LIMIT_MB} MB."
        )
        
    finally:
        # Stop tracing
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Log results for debugging if needed
        print(f"Streaming completed. Processed {count} rows.")
        print(f"Max memory observed: {max_memory_observed / (1024*1024):.2f} MB")
        print(f"Peak memory: {peak / (1024*1024):.2f} MB")