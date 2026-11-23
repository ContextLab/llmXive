import pytest
import numpy as np
from code.uq.metrics import expected_calibration_error, interval_score, sharpness

def test_ece():
    """Test ECE calculation logic with known inputs."""
    predictions = np.array([0.1, 0.4, 0.6, 0.9])
    variances = np.array([0.01, 0.04, 0.04, 0.01])
    targets = np.array([0.15, 0.35, 0.65, 0.85])
    
    # ECE should be a non-negative float
    ece = expected_calibration_error(predictions, variances, targets, n_bins=3)
    assert isinstance(ece, float)
    assert ece >= 0

def test_interval_score():
    """Test Interval Score calculation logic."""
    predictions = np.array([0.1, 0.9])
    variances = np.array([0.01, 0.01])
    targets = np.array([0.15, 0.85])
    
    # Calculate bounds for 90% interval (alpha=0.1)
    lower_90 = predictions - 1.645 * np.sqrt(variances)
    upper_90 = predictions + 1.645 * np.sqrt(variances)
    
    score = interval_score(lower_90, upper_90, targets, alpha=0.1)
    assert isinstance(score, float)
    assert score >= 0

def test_sharpness():
    """Test Sharpness calculation logic."""
    variances = np.array([0.01, 0.04, 0.09])
    score = sharpness(variances)
    assert isinstance(score, float)
    assert score >= 0

def test_ece_edge_cases():
    """Test ECE with edge cases: perfect calibration."""
    # If predictions match targets exactly and variance is small, ECE should be near 0
    predictions = np.array([0.2, 0.5, 0.8])
    variances = np.array([0.01, 0.01, 0.01])
    targets = np.array([0.2, 0.5, 0.8])
    
    ece = expected_calibration_error(predictions, variances, targets, n_bins=2)
    assert ece == 0.0

def test_interval_score_edge_cases():
    """Test Interval Score when target is within bounds."""
    predictions = np.array([0.5])
    variances = np.array([0.04])
    targets = np.array([0.5])
    
    lower = predictions - 1.645 * np.sqrt(variances)
    upper = predictions + 1.645 * np.sqrt(variances)
    
    score = interval_score(lower, upper, targets, alpha=0.1)
    # Score should be the width of the interval when target is covered
    expected_width = 2 * 1.645 * np.sqrt(0.04)
    assert np.isclose(score, expected_width)

def test_sharpness_single_value():
    """Test Sharpness with a single variance value."""
    variances = np.array([0.25])
    score = sharpness(variances)
    assert isinstance(score, float)
    assert score == 0.25