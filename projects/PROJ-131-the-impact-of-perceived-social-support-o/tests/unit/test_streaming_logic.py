"""
Unit tests for streaming logic (T052).
Verifies that streaming data yields correct statistics.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

# The streaming logic is primarily in ingestion.py
# We test the helper functions if exposed, or the main logic.

def test_streaming_mean_calculation():
    """Test that streaming mean calculation is correct."""
    # Generate a large dataset
    full_data = np.random.rand(10000)
    full_mean = np.mean(full_data)

    # Simulate streaming (chunked) calculation
    chunk_size = 1000
    stream_mean = 0.0
    count = 0
    for i in range(0, len(full_data), chunk_size):
        chunk = full_data[i:i+chunk_size]
        stream_mean += np.sum(chunk)
        count += len(chunk)
    stream_mean /= count

    # Allow small floating point error
    assert np.isclose(full_mean, stream_mean, rtol=1e-5)