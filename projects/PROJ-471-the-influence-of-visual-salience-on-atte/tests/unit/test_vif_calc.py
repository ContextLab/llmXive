"""
Unit tests for VIF Calculation (T030).
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Mock the config and paths
from unittest.mock import patch, MagicMock

# Import the function to test
# We need to import the module, but it relies on config.
# We will test the core logic function `calculate_vif` directly if possible,
# or mock the dependencies.

# Since the main function relies on file I/O, we test the logic function.
# We need to import the module.
# To avoid import errors due to missing config files in test env, we mock config.

@pytest.fixture
def mock_config():
    return {
        "paths": {
            "interim": Path(tempfile.gettempdir()),
            "processed": Path(tempfile.gettempdir()),
            "raw": Path(tempfile.gettempdir())
        }
    }

def test_calculate_vif_low_collinearity():
    """
    Test VIF calculation when features are NOT collinear with target.
    """
    # Create a dataframe with low correlation
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'luminance': np.random.rand(n),
        'contrast': np.random.rand(n),
        'edge_density': np.random.rand(n),
        'salience_score': np.random.rand(n) # Independent random noise
    })

    # Import the function from the module
    # We need to handle the import carefully if the module has side effects
    # But here we assume the function is pure enough.
    from code.analysis.vif_calc import calculate_vif

    vif_results = calculate_vif(df, ['luminance', 'contrast', 'edge_density'], 'salience_score')

    assert 'salience_score' in vif_results
    # With random data, R^2 should be low, so VIF should be close to 1
    assert vif_results['salience_score'] < 2.0  # VIF close to 1 means low collinearity
    assert vif_results['salience_score_r_squared'] < 0.1

def test_calculate_vif_high_collinearity():
    """
    Test VIF calculation when target is highly collinear with features.
    """
    np.random.seed(42)
    n = 100
    # Create features
    x1 = np.random.rand(n)
    x2 = np.random.rand(n)
    x3 = np.random.rand(n)
    # Target is a linear combination of features + small noise
    y = 2 * x1 + 3 * x2 - 1.5 * x3 + np.random.normal(0, 0.01, n)

    df = pd.DataFrame({
        'luminance': x1,
        'contrast': x2,
        'edge_density': x3,
        'salience_score': y
    })

    from code.analysis.vif_calc import calculate_vif

    vif_results = calculate_vif(df, ['luminance', 'contrast', 'edge_density'], 'salience_score')

    assert 'salience_score' in vif_results
    # R^2 should be very high, so VIF should be large (> 5)
    assert vif_results['salience_score'] > 5.0
    assert vif_results['salience_score_r_squared'] > 0.9

def test_calculate_vif_insufficient_data():
    """
    Test VIF calculation with too few data points.
    """
    df = pd.DataFrame({
        'luminance': [1.0, 2.0],
        'contrast': [1.0, 2.0],
        'edge_density': [1.0, 2.0],
        'salience_score': [1.0, 2.0]
    })

    from code.analysis.vif_calc import calculate_vif

    with pytest.raises(ValueError, match="Insufficient data"):
        calculate_vif(df, ['luminance', 'contrast', 'edge_density'], 'salience_score')

def test_vif_report_generation(mock_config):
    """
    Test that the report is written correctly.
    """
    import code.analysis.vif_calc as vif_module
    from code.analysis.vif_calc import write_vif_report

    vif_results = {
        'salience_score': 10.5,
        'salience_score_r_squared': 0.90
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config["paths"]["interim"] = Path(tmpdir)

        output_path = write_vif_report(vif_results, mock_config)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            report = json.load(f)

        assert report['status'] == 'completed'
        assert report['vif_values']['salience_score'] == 10.5
        assert report['threshold'] == 5.0
        assert 'interpretation' in report