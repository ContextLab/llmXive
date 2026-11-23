"""
tests/unit/test_resource_monitoring.py
Unit tests for resource monitoring integration in preprocessing and entropy scripts.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import functions to test
# Note: We test the logic, not the full file execution which requires data
from utils.resource_monitor import get_memory_usage_gb, check_resource_limits, log_resource_snapshot

def test_get_memory_usage_gb_returns_float():
    """Test that memory usage returns a float."""
    mem = get_memory_usage_gb()
    assert isinstance(mem, float)
    assert mem >= 0.0

def test_check_resource_limits_no_raise_under_limit():
    """Test that check_resource_limits does not raise when under limit."""
    # Mock the memory usage to be low
    with patch('utils.resource_monitor.get_memory_usage_gb', return_value=2.0):
        try:
            check_resource_limits(max_ram_gb=7.0)
            # If we are here, no exception was raised
            assert True
        except MemoryError:
            pytest.fail("check_resource_limits raised MemoryError unexpectedly")

def test_check_resource_limits_raises_over_limit():
    """Test that check_resource_limits raises when over limit."""
    # Mock the memory usage to be high
    with patch('utils.resource_monitor.get_memory_usage_gb', return_value=8.0):
        with pytest.raises(MemoryError):
            check_resource_limits(max_ram_gb=7.0)

def test_log_resource_snapshot_creates_file():
    """Test that log_resource_snapshot creates the log file."""
    import tempfile
    import shutil
    from pathlib import Path
    
    tmpdir = tempfile.mkdtemp()
    try:
        log_path = Path(tmpdir) / "test_resource.log"
        log_resource_snapshot("test", str(log_path))
        assert log_path.exists()
    finally:
        shutil.rmtree(tmpdir)
