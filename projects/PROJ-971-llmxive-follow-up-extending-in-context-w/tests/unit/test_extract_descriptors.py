"""
Unit tests for the descriptor extraction script (src/pipeline/extract_descriptors.py).

The tests focus on the pure‑Python helper functions that compute the three
statistical descriptors.  They operate on synthetic token matrices – this is
acceptable because the functions themselves are deterministic and do not rely
on the external ICWM encoder.
"""

import numpy as np
import pytest

from src.pipeline.extract_descriptors import (
    _variance,
    _lag1_autocorrelation,
    _mean_spectral_density,
)

def test_variance_simple():
    tokens = np.array([[1.0, 2.0], [3.0, 4.0]])
    # variance of all four numbers = 1.25
    assert pytest.approx(_variance(tokens), rel=1e-6) == 1.25

def test_lag1_autocorrelation_constant_series():
    # Constant series should yield 0.0 (handled as special case)
    tokens = np.ones((10, 3))
    assert _lag1_autocorrelation(tokens) == 0.0

def test_lag1_autocorrelation_known():
    # For a simple increasing series the lag‑1 autocorrelation is 1.0
    tokens = np.arange(10).reshape(-1, 1).astype(float)
    assert pytest.approx(_lag1_autocorrelation(tokens), rel=1e-6) == 1.0

def test_mean_spectral_density_zero_length():
    # With a single timestep the function returns 0.0 (guard clause)
    tokens = np.random.rand(1, 5)
    assert _mean_spectral_density(tokens) == 0.0

def test_mean_spectral_density_consistency():
    # For a sinusoidal signal the PSD should be > 0
    t = np.linspace(0, 1, 256)
    sin_signal = np.sin(2 * np.pi * 5 * t)  # 5 Hz sine wave
    tokens = sin_signal.reshape(-1, 1)
    psd = _mean_spectral_density(tokens)
    assert psd > 0.0