"""
Tests for checksum functionality.
"""
import pytest
from data_generation.utils import compute_checksum
import hashlib

def test_checksum_deterministic():
    """Checksum should be deterministic."""
    data = "test string"
    c1 = compute_checksum(data)
    c2 = compute_checksum(data)
    assert c1 == c2

def test_checksum_unique():
    """Different data should have different checksums."""
    c1 = compute_checksum("data1")
    c2 = compute_checksum("data2")
    assert c1 != c2
