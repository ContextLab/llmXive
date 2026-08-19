"""
Unit tests for the memory-efficient data loader.
Specifically tests the peak memory usage constraint on a synthetic stream.
"""
import os
import sys
import gc
import tempfile
import pytest
import csv

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.lib.data_loader import (
    create_synthetic_moderate_stream, 
    get_current_memory_gb, 
    RAM_LIMIT_GB, 
    log_memory_usage
)

class TestMemoryLoader:
    """Tests for memory constraints and streaming logic."""

    def test_peak_memory_under_limit_on_synthetic_stream(self):
        """
        Asserts that peak memory usage stays below 7GB when processing
        a synthetic Moderate-sized stream.
        """
        # Ensure we start with a clean state
        gc.collect()
        
        # We will track the max memory observed during the stream
        max_memory_gb = 0.0
        
        # Generate a synthetic stream of moderate size
        # 10,000 items of ~1000 tokens each is a good stress test
        # without requiring the full RULER dataset
        stream = create_synthetic_moderate_stream(n_items=10000)
        
        for item in stream:
            # Force a memory check periodically
            if item['id'] % 1000 == 0:
                gc.collect()
                current_mem = get_current_memory_gb()
                if current_mem > max_memory_gb:
                    max_memory_gb = current_mem
        
        # Final check
        gc.collect()
        final_mem = get_current_memory_gb()
        if final_mem > max_memory_gb:
            max_memory_gb = final_mem

        # Assert the constraint
        # We use a slightly loose margin for the test environment, 
        # but strictly < 7GB as per requirements
        assert max_memory_gb < RAM_LIMIT_GB, (
            f"Peak memory usage {max_memory_gb:.2f}GB exceeded limit of {RAM_LIMIT_GB}GB. "
            f"Stream processing may not be memory-efficient enough."
        )

    def test_memory_log_file_created(self):
        """Verifies that the memory profile CSV is created and populated."""
        # Clear any existing log file for a clean test
        log_path = "data/logs/memory_profile.csv"
        if os.path.exists(log_path):
            os.remove(log_path)
        
        # Run a small stream to generate logs
        list(create_synthetic_moderate_stream(n_items=500))
        
        # Verify file existence
        assert os.path.exists(log_path), "Memory profile CSV was not created."
        
        # Verify content
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0, "Memory profile CSV is empty."
            
            # Check required columns
            required_cols = {'timestamp', 'step', 'memory_gb', 'limit_gb', 'status'}
            assert required_cols.issubset(set(rows[0].keys())), "Missing required columns in log."

    def test_stream_yields_correct_structure(self):
        """Verifies that the synthetic stream yields dictionaries with expected keys."""
        stream = create_synthetic_moderate_stream(n_items=5)
        for item in stream:
            assert isinstance(item, dict)
            assert 'id' in item
            assert 'text' in item
            assert 'tokens' in item
            assert 'length' in item
            assert len(item['tokens']) == item['length']