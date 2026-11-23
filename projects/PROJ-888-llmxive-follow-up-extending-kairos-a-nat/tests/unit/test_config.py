"""
Unit tests for code/config.py.
"""
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import pytest
from config import (
    SEED,
    QUANTIZATION_LEVELS,
    NOISE_STDS,
    SUBSET_SIZE,
    MAX_RAM_GB,
    INFER_HORIZONS,
    QUANTIZATION_LEVELS,
    set_seed,
    get_config_summary
)

def test_quantization_levels():
    """Test that quantization levels match FR-001 requirements."""
    assert QUANTIZATION_LEVELS == [4, 6, 8, 16]

def test_noise_stds():
    """Test that noise std devs are valid."""
    assert all(isinstance(x, (int, float)) and x >= 0 for x in NOISE_STDS)

def test_subset_size():
    """Test that subset size is a positive integer."""
    assert isinstance(SUBSET_SIZE, int)
    assert SUBSET_SIZE > 0

def test_inference_horizons():
    """Test that inference horizons match spec (100, 500, 1000)."""
    assert INFER_HORIZONS == [100, 500, 1000]

def test_set_seed():
    """Test that set_seed initializes random state."""
    import random
    import numpy as np
    set_seed(123)
    val1 = random.random()
    set_seed(123)
    val2 = random.random()
    assert val1 == val2

def test_get_config_summary():
    """Test that config summary returns expected keys."""
    summary = get_config_summary()
    assert "seed" in summary
    assert "quantization_levels" in summary
    assert "paths" in summary
    assert summary["quantization_levels"] == [4, 6, 8, 16]