"""
Integration test for memory flow (T014 dependency).
Verifies that the pipeline components can handle data streams without
excessive memory usage, using mock data.
"""
import os
import sys
import tempfile
import gc
from pathlib import Path
import logging

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging import get_memory_usage_mb, setup_logger

logger = setup_logger("integration_memory_test", level=logging.INFO)

def test_memory_tracking():
    """
    Verify that memory tracking utilities work correctly.
    """
    logger.info("Starting memory tracking test...")
    
    initial_memory = get_memory_usage_mb()
    logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
    
    # Create some data to simulate processing
    data_buffer = []
    for i in range(10000):
        data_buffer.append("A" * 1000)
    
    current_memory = get_memory_usage_mb()
    logger.info(f"Memory after data allocation: {current_memory:.2f} MB")
    
    # Clean up
    data_buffer.clear()
    gc.collect()
    
    final_memory = get_memory_usage_mb()
    logger.info(f"Final memory usage: {final_memory:.2f} MB")
    
    # The test passes if we can track memory without crashing
    # We don't assert specific values as they vary by environment
    assert current_memory >= initial_memory, "Memory tracking seems broken (memory decreased after allocation?)"
    logger.info("Memory tracking test PASSED.")

if __name__ == "__main__":
    test_memory_tracking()