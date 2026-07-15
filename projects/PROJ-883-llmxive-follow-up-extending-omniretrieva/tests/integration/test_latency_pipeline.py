"""
Integration test for end-to-end query execution loop with CPU throttling.
"""
import pytest
import os
import sys
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from utils.cpu_throttle import check_throttling_validity, throttled_context, ThrottleError
from generators.synthetic_query import SyntheticQueryGenerator

def test_throttling_validity():
    """Test that throttling validity check passes."""
    assert check_throttling_validity() is True

def test_execution_with_throttling():
    """Test that execution completes within throttled context."""
    if not check_throttling_validity():
        pytest.skip("Throttling not available")
    
    generator = SyntheticQueryGenerator(seed=42)
    query = generator.generate_query("text", 2)
    
    start = time.time()
    try:
        with throttled_context(cpu_limit_seconds=5.0, memory_limit_mb=256):
            time.sleep(0.1) # Simulate work
    except ThrottleError:
        pytest.fail("Throttling error occurred unexpectedly")
    
    elapsed = time.time() - start
    assert elapsed < 5.0
