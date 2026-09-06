"""
Integration test for T026: Verify that aggregate_robustness_metrics produces a valid CSV
containing expected columns when prerequisite files exist.
"""

import pandas as pd
import pytest
import tempfile
import os
from pathlib import Path

# Mock the config_manager to use temp directories
# This is necessary because the real config points to project root which might not be set up in CI
# In a real CI environment, this would be configured via environment variables or fixtures.
# For this test, we patch the functions.

import aggregate_robustness
from unittest.mock import patch, MagicMock


@pytest.fixture
def temp_results_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        # Create prerequisite files
        # Bootstrap
        (results_dir / "bootstrap_results.csv").write_text(
            "interaction_coef,interaction_ci_lower,interaction_ci_upper,interaction_p_val,interaction_se\n0.5,0.1,0.9,0.03,0.2\n"
        )
        # Alpha Sweep
        (results_dir / "alpha_sweep.csv").write_text(
            "alpha_level,significant\n0.01,False\n0.05,True\n0.10,True\n"
        )
        # Covariate
        (results_dir / "covariate_adjustment.csv").write_text(
            "interaction_coef,interaction_p_val\n0.4,0.04\n"
        )
        # Binary Model
        (results_dir / "binary_model_results.csv").write_text(
            "interaction_coef,interaction_p_val\n0.3,0.06\n"
        )
        # Primary Model (for stability ratio)
        (results_dir / "primary_model_results.csv").write_text(
            "interaction_coef,interaction_p_val\n0.5,0.03\n"
        )

        yield results_dir


@patch('aggregate_robustness.get_results_path')
def test_aggregate_robustness_creates_csv(mock_get_path, temp_results_dir):
    mock_get_path.return_value = temp_results_dir

    # Run the aggregation
    df = aggregate_robustness.aggregate_robustness_metrics()

    # Verify output file exists
    output_path = temp_results_dir / "robustness_metrics.csv"
    assert output_path.exists(), "robustness_metrics.csv was not created"

    # Verify content
    df_output = pd.read_csv(output_path)
    assert not df_output.empty, "Output CSV is empty"

    # Check for expected columns (subset of all possible)
    expected_cols = [
        'bootstrap_interaction_coef',
        'bootstrap_ci_lower',
        'alpha_sweep_005_significant',
        'covariate_interaction_coef',
        'binary_interaction_coef'
    ]

    for col in expected_cols:
        assert col in df_output.columns, f"Missing expected column: {col}"

    # Verify specific values
    row = df_output.iloc[0]
    assert row['bootstrap_interaction_coef'] == 0.5
    assert row['alpha_sweep_005_significant'] is True
    assert row['covariate_interaction_coef'] == 0.4
    assert row['binary_interaction_coef'] == 0.3
    # Stability ratio: 0.4 / 0.5 = 0.8
    assert abs(row['covariate_stability_ratio'] - 0.8) < 1e-6
