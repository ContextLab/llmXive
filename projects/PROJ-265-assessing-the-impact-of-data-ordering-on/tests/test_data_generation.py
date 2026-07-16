"""
Unit tests for AR(1) data generation.

Tests the generate_ar1 function to ensure it produces series with the 
correct autoregressive parameter (phi) and mean.
"""
import pytest
import numpy as np
from statsmodels.tsa.ar_model import AutoReg

# Import the function under test from the project's code module
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports during testing
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data_generation import generate_ar1
from config import get_data_seed


def test_generate_ar1_returns_correct_mean_and_phi():
    """
    Test that generate_ar1 produces a series with the specified phi and mean.
    
    Input:
        phi=0.8, n=100, seed=42
    
    Logic:
        1. Generate the AR(1) series.
        2. Estimate phi using statsmodels.tsa.ar_model.AutoReg.
        3. Calculate the mean of the series.
    
    Assertions:
        - The estimated phi is within 0.05 of the true phi (0.8).
        - The mean is within 0.01 of 0.0.
    """
    # Parameters
    phi_true = 0.8
    n = 100
    seed = 42
    
    # Generate the series
    data = generate_ar1(phi=phi_true, n=n, seed=seed)
    
    # Verify output type and shape
    assert isinstance(data, np.ndarray), "Output must be a numpy array"
    assert data.shape == (n,), f"Output shape must be ({n},)"
    
    # Estimate phi using AutoReg
    # AutoReg fits y_t = c + phi_1*y_{t-1} + ... + phi_k*y_{t-k} + e_t
    # We fit an AR(1) model (order=1)
    model = AutoReg(data, lags=1, old_names=False)
    result = model.fit()
    
    # The coefficient for the lag 1 term is the estimated phi
    # result.params[0] is the intercept (c), result.params[1] is the AR(1) coeff
    estimated_phi = result.params[1]
    
    # Calculate mean
    series_mean = np.mean(data)
    
    # Assertions with tolerances appropriate for n=100
    # Tolerance for phi: 0.05
    assert abs(estimated_phi - phi_true) < 0.05, (
        f"Estimated phi ({estimated_phi:.4f}) is not within 0.05 of true phi ({phi_true}). "
        f"Difference: {abs(estimated_phi - phi_true):.4f}"
    )
    
    # Tolerance for mean: 0.01
    # Note: For AR(1) with mean 0, the sample mean should be close to 0
    assert abs(series_mean - 0.0) < 0.01, (
        f"Series mean ({series_mean:.4f}) is not within 0.01 of 0.0. "
        f"Difference: {abs(series_mean):.4f}"
    )
    
    # Additional sanity checks
    assert not np.any(np.isnan(data)), "Data contains NaN values"
    assert not np.any(np.isinf(data)), "Data contains Inf values"