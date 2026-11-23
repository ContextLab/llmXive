"""
Unit tests for systematic uncertainty inflation test (T031).
"""
import pytest
import numpy as np
from pathlib import Path
import json

from robustness.uncertainty import inflate_covariance, main

def test_inflate_covariance():
    """Test that covariance matrix is inflated correctly."""
    cov = np.array([[1.0, 0.5], [0.5, 1.0]])
    factor = 2.0
    inflated = inflate_covariance(cov, factor)
    
    expected = cov * (factor ** 2)
    np.testing.assert_array_almost_equal(inflated, expected)

def test_inflate_covariance_factor_one():
    """Test that factor of 1.0 leaves matrix unchanged."""
    cov = np.array([[1.0, 0.5], [0.5, 1.0]])
    inflated = inflate_covariance(cov, 1.0)
    np.testing.assert_array_almost_equal(inflated, cov)

# Note: Full integration test for main() would require real data and nested sampling.
# This is covered by integration tests in tests/integration/test_robustness.py (T029).