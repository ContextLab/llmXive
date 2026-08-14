"""
Tests for T010b: Exclusion Logic.
"""
import os
import sys
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from config import get_path, ensure_dirs, get_exclusion_params
from utils.eeg_helpers import reject_channels_by_variance

def test_exclusion_threshold_logic():
    """Test that the exclusion threshold logic works correctly."""
    # Simulate the logic
    threshold = get_exclusion_params()['max_channel_rejection_ratio']
    
    # Case 1: 0 rejected out of 20 -> 0.0 <= 0.30 -> Kept
    assert (0 / 20) <= threshold
    
    # Case 2: 6 rejected out of 20 -> 0.30 <= 0.30 -> Kept
    assert (6 / 20) <= threshold
    
    # Case 3: 7 rejected out of 20 -> 0.35 > 0.30 -> Excluded
    assert (7 / 20) > threshold

def test_ensure_dirs_accepts_list():
    """Test that ensure_dirs accepts a list of paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "a"
        p2 = Path(tmpdir) / "b"
        ensure_dirs([p1, p2])
        assert p1.exists()
        assert p2.exists()

def test_get_path_variations():
    """Test get_path with various argument shapes."""
    # Single key
    p1 = get_path("data_interim")
    assert isinstance(p1, Path)
    
    # Single relative
    p2 = get_path("data/raw")
    assert isinstance(p2, Path)
    
    # Two args (key, rel)
    p3 = get_path("data_interim", "test.csv")
    assert isinstance(p3, Path)
    
    # Two args (rel, rel)
    p4 = get_path("data", "processed")
    assert isinstance(p4, Path)