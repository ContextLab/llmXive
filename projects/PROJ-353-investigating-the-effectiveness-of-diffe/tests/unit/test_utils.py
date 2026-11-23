"""
Unit tests for code/utils.py
"""
import pytest
import os
import tempfile
from pathlib import Path

from utils import (
    seed_all,
    hash_artifact,
    SAMPLE_SIZE,
    CONVERGENCE_THRESHOLD,
    MAX_EPOCHS
)

def test_sample_size_is_110():
    """Verify SAMPLE_SIZE constant matches specification (FR-001)."""
    assert SAMPLE_SIZE == 110

def test_convergence_threshold_is_090():
    """Verify CONVERGENCE_THRESHOLD constant matches specification (FR-005)."""
    assert CONVERGENCE_THRESHOLD == 0.90

def test_max_epochs_is_1000():
    """Verify MAX_EPOCHS constant matches specification (FR-005)."""
    assert MAX_EPOCHS == 1000

def test_seed_all_sets_random_seed():
    """Verify seed_all sets the random module seed."""
    import random
    seed_all(12345)
    val1 = random.random()
    
    seed_all(12345)
    val2 = random.random()
    
    assert val1 == val2, "Random seed not set correctly"

def test_seed_all_sets_numpy_seed():
    """Verify seed_all sets numpy seed if available."""
    try:
        import numpy as np
        seed_all(67890)
        arr1 = np.random.rand(5)
        
        seed_all(67890)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2), "Numpy seed not set correctly"
    except ImportError:
        pytest.skip("NumPy not installed")

def test_seed_all_sets_torch_seed():
    """Verify seed_all sets torch seed if available."""
    try:
        import torch
        seed_all(11223)
        t1 = torch.rand(5)
        
        seed_all(11223)
        t2 = torch.rand(5)
        
        assert torch.equal(t1, t2), "Torch seed not set correctly"
    except ImportError:
        pytest.skip("PyTorch not installed")

def test_hash_artifact_returns_sha256():
    """Verify hash_artifact computes correct SHA-256 hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        import hashlib
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        actual_hash = hash_artifact(temp_path)
        
        assert actual_hash == expected_hash, "Hash mismatch"
    finally:
        os.unlink(temp_path)

def test_hash_artifact_raises_on_missing_file():
    """Verify hash_artifact raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        hash_artifact("/nonexistent/path/file.txt")