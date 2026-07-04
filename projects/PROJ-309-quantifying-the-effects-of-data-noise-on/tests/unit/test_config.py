"""Unit tests for configuration constants and enums."""
import pytest
from config import NoiseType, get_snr_levels, get_seeds, get_system_params


def test_noise_type_enum():
    """Verify NoiseType enum has expected values."""
    assert NoiseType.GAUSSIAN.value == "gaussian"
    assert NoiseType.QUANTIZATION.value == "quantization"


def test_get_snr_levels():
    """Verify SNR levels are returned as a list of floats."""
    levels = get_snr_levels()
    assert isinstance(levels, list)
    assert all(isinstance(s, (int, float)) for s in levels)
    assert len(levels) > 0


def test_get_seeds():
    """Verify seeds are returned as a list of integers."""
    seeds = get_seeds()
    assert isinstance(seeds, list)
    assert all(isinstance(s, int) for s in seeds)
    assert len(seeds) > 0


def test_get_system_params():
    """Verify system parameters are returned as a dictionary."""
    params = get_system_params()
    assert isinstance(params, dict)
    assert "lorenz" in params
    assert "rossler" in params
