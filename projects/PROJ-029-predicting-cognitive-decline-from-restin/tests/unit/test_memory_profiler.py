"""
Unit tests for memory profiling utilities.
"""
import pytest
import psutil
import os
from utils.memory_profiler import get_peak_memory_gb

def test_get_peak_memory_gb():
    """Test that memory profiler returns a positive float."""
    # This test runs in the current process
    mem_gb = get_peak_memory_gb()
    assert mem_gb >= 0.0
    assert isinstance(mem_gb, float)
