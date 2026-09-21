"""
Unit tests for T042: Interval Score artifact generation.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generate_interval_scores import calculate_interval_scores, load_interval_outputs
from metrics import interval_score


def test_interval_score_calculation():
    """Test that interval scores are calculated correctly and are non-negative."""
    # Create a mock dataframe
    data = {
        'series_id': ['S1', 'S1', 'S2'],
        'model': ['ARIMA', 'ARIMA', 'Prophet'],
        'horizon': [1, 2, 1],
        'lower': [0.8, 0.9, 0.5],
        'upper': [1.2, 1.1, 1.5],
        'actual': [1.0, 1.05, 1.0],
        'nominal_level': [0.95, 0.95, 0.90]
    }
    df = pd.DataFrame(data)

    result = calculate_interval_scores(df)

    assert 'interval_score' in result.columns
    assert len(result) == len(df)
    assert all(result['interval_score'] >= 0), "Interval scores must be non-negative"


def test_interval_score_formula():
    """Verify the interval score formula manually for a specific case."""
    # alpha = 0.05 (95% interval)
    # lower = 0, upper = 2, actual = 1 (inside) -> Score = width = 2
    # lower = 0, upper = 2, actual = 3 (outside) -> Score = width + 2/alpha * (actual - upper) = 2 + 40 * 1 = 42
    # lower = 0, upper = 2, actual = -1 (outside) -> Score = width + 2/alpha * (lower - actual) = 2 + 40 * 1 = 42

    score_inside = interval_score(0.0, 2.0, 1.0, alpha=0.05)
    assert np.isclose(score_inside, 2.0), f"Expected 2.0 for inside, got {score_inside}"

    score_outside_high = interval_score(0.0, 2.0, 3.0, alpha=0.05)
    expected_high = 2.0 + (2.0 / 0.05) * (3.0 - 2.0)
    assert np.isclose(score_outside_high, expected_high), f"Expected {expected_high}, got {score_outside_high}"

    score_outside_low = interval_score(0.0, 2.0, -1.0, alpha=0.05)
    expected_low = 2.0 + (2.0 / 0.05) * (0.0 - (-1.0))
    assert np.isclose(score_outside_low, expected_low), f"Expected {expected_low}, got {score_outside_low}"


def test_missing_columns():
    """Test that missing required columns raise an error."""
    data = {
        'series_id': ['S1'],
        'model': ['ARIMA'],
        'horizon': [1],
        'lower': [0.8],
        'upper': [1.2],
        'actual': [1.0]
        # Missing 'nominal_level'
    }
    df = pd.DataFrame(data)

    with pytest.raises(ValueError, match="missing.*nominal_level.*alpha"):
        calculate_interval_scores(df)