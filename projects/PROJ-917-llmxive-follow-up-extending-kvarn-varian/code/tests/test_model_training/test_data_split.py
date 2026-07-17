"""
Tests for train/test split logic.
"""
import pytest
import numpy as np

def test_split_sizes():
    """Test that split sizes are correct."""
    data = np.random.rand(100, 4)
    train_size = int(0.8 * len(data))
    train = data[:train_size]
    test = data[train_size:]
    assert len(train) == 80
    assert len(test) == 20
