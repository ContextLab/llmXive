import pytest
import numpy as np
from code.uq.metrics import expected_calibration_error, interval_score, sharpness

def test_ece():
    predictions = np.array([0.1, 0.4, 0.6, 0.9])
    variances = np.array([0.01, 0.04, 0.04, 0.01])
    targets = np.array([0.15, 0.35, 0.65, 0.85])
    ece = expected_calibration_error(predictions, variances, targets, n_bins=3)
    assert isinstance(ece, float)
    assert ece >= 0

def test_interval_score():
    predictions = np.array([0.1, 0.9])
    variances = np.array([0.01, 0.01])
    targets = np.array([0.15, 0.85])
    lower_90 = predictions - 1.645 * np.sqrt(variances)
    upper_90 = predictions + 1.645 * np.sqrt(variances)
    score = interval_score(lower_90, upper_90, targets, alpha=0.1)
    assert isinstance(score, float)
    assert score >= 0

def test_sharpness():
    variances = np.array([0.01, 0.04, 0.09])
    score = sharpness(variances)
    assert isinstance(score, float)
    assert score >= 0
