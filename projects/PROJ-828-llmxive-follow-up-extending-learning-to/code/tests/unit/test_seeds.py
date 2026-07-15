"""
Unit tests for the seeds.py module.
"""

import pytest
import random
import os

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.seeds import (
    set_seed,
    generate_seed_from_string,
    get_seed_config,
    apply_seed_config,
    HAS_NUMPY,
    HAS_TORCH
)


def test_set_seed_python():
    """Test that Python random seed is set correctly."""
    seed = 42
    result = set_seed(seed)
    assert result["seed"] == seed
    assert result["python"] is True

    # Verify reproducibility
    val1 = random.random()
    set_seed(seed)
    val2 = random.random()
    assert val1 == val2


def test_set_seed_numpy():
    """Test that NumPy random seed is set correctly if available."""
    if not HAS_NUMPY:
        pytest.skip("NumPy not available")

    import numpy as np
    seed = 123
    result = set_seed(seed)
    assert result["numpy"] is True

    # Verify reproducibility
    arr1 = np.random.rand(5)
    set_seed(seed)
    arr2 = np.random.rand(5)
    assert np.array_equal(arr1, arr2)


def test_set_seed_torch():
    """Test that PyTorch random seed is set correctly if available."""
    if not HAS_TORCH:
        pytest.skip("PyTorch not available")

    import torch
    seed = 456
    result = set_seed(seed)
    assert result["torch"] is True

    # Verify reproducibility
    t1 = torch.rand(5)
    set_seed(seed)
    t2 = torch.rand(5)
    assert torch.equal(t1, t2)


def test_deterministic_mode():
    """Test that deterministic mode is set when requested."""
    seed = 789
    result = set_seed(seed, deterministic=True)
    assert result["deterministic_mode"] is True

    if HAS_TORCH:
        import torch
        assert torch.backends.cudnn.deterministic is True
        assert torch.backends.cudnn.benchmark is False


def test_environment_variable_set():
    """Test that PYTHONHASHSEED environment variable is set."""
    seed = 999
    set_seed(seed)
    assert os.environ.get("PYTHONHASHSEED") == str(seed)


def test_generate_seed_from_string():
    """Test deterministic seed generation from strings."""
    seed1 = generate_seed_from_string("experiment_a")
    seed2 = generate_seed_from_string("experiment_a")
    seed3 = generate_seed_from_string("experiment_b")

    assert seed1 == seed2
    assert seed1 != seed3
    assert isinstance(seed1, int)
    assert 0 <= seed1 < 2**32


def test_generate_seed_with_offset():
    """Test seed generation with offset."""
    base = generate_seed_from_string("test")
    with_offset = generate_seed_from_string("test", offset=100)
    assert base != with_offset


def test_get_seed_config():
    """Test seed configuration generation."""
    config = get_seed_config(42)
    assert config["base_seed"] == 42
    assert config["deterministic"] is True
    assert config["torch_deterministic"] is True
    assert config["torch_cudnn_benchmark"] is False


def test_apply_seed_config():
    """Test applying a seed configuration."""
    config = get_seed_config(12345)
    result = apply_seed_config(config)

    assert result["seed"] == 12345
    assert result["python"] is True

    if HAS_NUMPY:
        assert result["numpy"] is True
    if HAS_TORCH:
        assert result["torch"] is True
