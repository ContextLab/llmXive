"""
Unit tests for utility functions.

Verifies seeding, file I/O, and checksum calculations.
"""
import pytest
import os
import json
import tempfile
import sys
from pathlib import Path

# Ensure code/ is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils import set_seed, calculate_checksum, load_json, save_json, ensure_directory

def test_set_seed_reproducibility():
    """Test that set_seed produces reproducible random numbers."""
    set_seed(123)
    val1 = os.urandom(4) # os.urandom is not seeded by random.seed, but we test our wrapper logic if it uses np.random
    
    # Test with numpy (commonly used in utils)
    import numpy as np
    set_seed(456)
    arr1 = np.random.rand(5)
    
    set_seed(456)
    arr2 = np.random.rand(5)
    
    assert np.array_equal(arr1, arr2), "Seed not reproducible for numpy"

def test_checksum_consistency():
    """Test that the same content produces the same checksum."""
    content = b"test data for checksum"
    checksum1 = calculate_checksum(content)
    checksum2 = calculate_checksum(content)
    assert checksum1 == checksum2, "Checksums should be identical for same content"

def test_save_load_json():
    """Test JSON save and load roundtrip."""
    data = {"key": "value", "number": 42}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        save_json(data, temp_path)
        loaded = load_json(temp_path)
        assert loaded == data, "Loaded JSON does not match saved data"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_ensure_directory():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = os.path.join(tmpdir, "sub", "nested", "dir")
        ensure_directory(new_dir)
        assert os.path.isdir(new_dir), "Directory was not created"
