"""
Unit tests for memory profiling utilities.
"""
import pytest
import sys
from pathlib import Path
import tracemalloc
import gc

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils import set_seed

def test_memory_profiling_basic():
    """Test basic memory profiling functionality."""
    tracemalloc.start()
    
    # Allocate some memory
    data = [i for i in range(10000)]
    
    current, peak = tracemalloc.get_traced_memory()
    
    # Verify we have some memory usage
    assert current > 0
    assert peak > 0
    assert peak >= current
    
    tracemalloc.stop()
    del data
    gc.collect()

def test_memory_profiling_cleanup():
    """Test that memory is released after cleanup."""
    tracemalloc.start()
    
    # Allocate memory
    data = [i for i in range(100000)]
    current_before, peak_before = tracemalloc.get_traced_memory()
    
    # Delete and collect
    del data
    gc.collect()
    
    current_after, peak_after = tracemalloc.get_traced_memory()
    
    # Current should be lower after cleanup
    assert current_after < current_before
    
    tracemalloc.stop()

def test_get_peak_memory_helper():
    """Test the helper function for getting peak memory."""
    def get_peak_memory_mb():
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    
    tracemalloc.start()
    
    # Allocate memory
    data = [i for i in range(10000)]
    
    peak_mb = get_peak_memory_mb()
    
    # Should be a positive number
    assert peak_mb > 0
    assert peak_mb < 1000  # Reasonable upper bound for this test
    
    tracemalloc.stop()
    del data
    gc.collect()