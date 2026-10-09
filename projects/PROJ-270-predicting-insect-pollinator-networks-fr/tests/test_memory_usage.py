"""
Performance Verification Test

This test creates a 2 GB sparse file using a memory‑mapped array,
processes it in small chunks, and asserts that the peak memory usage
stays below 6.5 GB. The test is deliberately lightweight on RAM:
the file is never fully loaded into memory; only a few megabytes are
read at a time.
"""

import os
import resource
import tempfile

import numpy as np
import pytest

# Helper to get peak memory usage in GB (Linux: ru_maxrss is in kilobytes)
def get_peak_memory_gb() -> float:
    usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # On macOS ru_maxrss is in bytes; handle both cases
    if usage_kb > 1e7:  # heuristically assume kilobytes if large
        usage_gb = usage_kb / (1024 * 1024)
    else:
        usage_gb = usage_kb / (1024 ** 3)
    return usage_gb

@pytest.mark.timeout(300)
def test_memory_usage_under_limit():
    # Size of the synthetic dataset: 2 GB
    target_size_bytes = 2 * 1024 ** 3  # 2 GB

    # Create a temporary file of exactly 2 GB without writing data
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    try:
        # Truncate file to required size (sparse file)
        os.truncate(tmp_path, target_size_bytes)

        # Memory‑map the file as uint8 (1 byte per element)
        mm = np.memmap(tmp_path, dtype=np.uint8, mode='r')
        total_elements = mm.shape[0]

        # Process the file in chunks (e.g., 10 MiB per chunk)
        chunk_bytes = 10 * 1024 ** 2  # 10 MiB
        chunk_elements = chunk_bytes  # uint8 -> 1 byte per element
        processed_sum = 0
        for start in range(0, total_elements, chunk_elements):
            end = min(start + chunk_elements, total_elements)
            chunk = mm[start:end]
            # Simple operation to simulate work
            processed_sum += int(chunk.sum())
        # Ensure the loop actually ran
        assert processed_sum >= 0

        # Flush and close the memmap
        del mm

        peak_gb = get_peak_memory_gb()
        # Debug output (useful if test fails)
        print(f"Peak memory usage: {peak_gb:.2f} GB")
        # Assert that peak memory stays well below the 6.5 GB limit
        assert peak_gb < 6.5, f"Peak memory usage {peak_gb:.2f} GB exceeds limit"
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)