"""
Unit tests for reproducibility seed enforcement (T063a).
"""
import os
import sys
import hashlib
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.utils.helpers import set_reproducibility_seed, is_seed_set
import random
import numpy as np

def generate_test_checksum(seed_value: int) -> str:
    """
    Run a small analysis pipeline and return a checksum of the output.
    Used to verify reproducibility.
    """
    # Set the seed
    set_reproducibility_seed(seed_value)
    
    # Generate some random data
    data1 = [random.random() for _ in range(100)]
    data2 = np.random.randn(100).tolist()
    
    # Compute a simple checksum
    combined = str(data1) + str(data2)
    return hashlib.sha256(combined.encode()).hexdigest()

def test_seed_determinism():
    """
    Test that running the same pipeline twice with the same seed
    produces identical checksums.
    """
    seed_value = 42
    
    checksum1 = generate_test_checksum(seed_value)
    checksum2 = generate_test_checksum(seed_value)
    
    assert checksum1 == checksum2, f"Checksums differ: {checksum1} vs {checksum2}"
    assert len(checksum1) == 64, "Invalid checksum length"

def test_seed_changes_output():
    """
    Test that different seeds produce different outputs.
    """
    checksum1 = generate_test_checksum(42)
    checksum2 = generate_test_checksum(123)
    
    assert checksum1 != checksum2, "Different seeds should produce different outputs"

def test_is_seed_set():
    """Test that is_seed_set returns True after setting a seed."""
    set_reproducibility_seed(42)
    assert is_seed_set(), "Seed should be marked as set"

def test_seed_from_env_var():
    """Test that seed is read from RANDOM_SEED env var if not provided."""
    os.environ['RANDOM_SEED'] = '999'
    set_reproducibility_seed()  # No argument
    
    # Verify the seed was set
    assert is_seed_set()
    
    # Clean up
    del os.environ['RANDOM_SEED']

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])