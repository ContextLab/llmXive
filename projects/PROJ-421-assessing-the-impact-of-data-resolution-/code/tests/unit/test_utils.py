"""Unit tests for utility functions in code/utils.py."""
import pytest
import os
import tempfile
import numpy as np
from utils import (
    checksum_file,
    get_raster_info,
    create_memory_mapped_array,
    RetryError,
    retry_with_backoff
)

def test_checksum_file():
    """Test that checksum_file returns a valid hex digest."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum = checksum_file(temp_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_checksum_file_unchanged():
    """Test that checksum is deterministic."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum1 = checksum_file(temp_path)
        checksum2 = checksum_file(temp_path)
        assert checksum1 == checksum2
    finally:
        os.unlink(temp_path)

def test_create_memory_mapped_array():
    """Test creation of memory mapped array."""
    shape = (100, 100)
    dtype = np.uint8
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name

    try:
        mmapped = create_memory_mapped_array(shape, dtype, temp_path)
        assert mmapped.shape == shape
        assert mmapped.dtype == dtype
        # Verify we can write and read
        mmapped[0, 0] = 42
        assert mmapped[0, 0] == 42
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_retry_with_backoff_success():
    """Test that retry_with_backoff returns on first try."""
    call_count = 0
    def succeed_immediately():
        nonlocal call_count
        call_count += 1
        return "success"

    result = retry_with_backoff(succeed_immediately, max_retries=3, delay=0.01)
    assert result == "success"
    assert call_count == 1

def test_retry_with_backoff_failure():
    """Test that retry_with_backoff raises RetryError after max retries."""
    call_count = 0
    def always_fail():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(RetryError):
        retry_with_backoff(always_fail, max_retries=2, delay=0.01)

    assert call_count == 3  # Initial + 2 retries

def test_retry_with_backoff_partial_success():
    """Test that retry_with_backoff succeeds after some failures."""
    call_count = 0
    def fail_twice_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "success"

    result = retry_with_backoff(fail_twice_then_succeed, max_retries=3, delay=0.01)
    assert result == "success"
    assert call_count == 3

def test_get_raster_info_missing_file():
    """Test that get_raster_info raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        get_raster_info("non_existent_file.tif")