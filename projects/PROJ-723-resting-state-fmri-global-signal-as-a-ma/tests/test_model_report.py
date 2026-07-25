"""
Tests for T025: model_report generation.

These tests verify that:
  1. The report generation logic runs without error.
  2. The report contains the required keys.
  3. The null distribution stats are computed correctly.
  4. The p-value calculation is correct.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Mock the modeling functions to avoid heavy computation in tests
@pytest.fixture
def mock_modeling_results():
    """Fixture to provide mock results from modeling functions."""
    return {
        "mean_mae": 2.5,
        "mean_r": 0.35,
        "mean_r2": 0.12,
        "optimal_alpha": 1.0,
    }

@pytest.fixture
def mock_null_results():
    """Fixture to provide mock null distribution results."""
    np.random.seed(42)
    null_maes = np.random.normal(loc=3.0, scale=0.5, size=1000)
    return {
        "null_maes": null_maes,
    }

@pytest.fixture
def mock_df():
    """Fixture to provide a mock cleaned data DataFrame."""
    data = {
        "Subject_ID": [f"sub-{i:03d}" for i in range(1, 11)],
        "Global_Signal_SD": np.random.rand(10) * 0.5,
        "MWQ_Score": np.random.randint(10, 50, 10),
        "Age": np.random.randint(20, 60, 10),
        "Sex": np.random.choice([0, 1], 10),
        "Mean_FD": np.random.rand(10) * 0.2,
        "Mean_DVARS": np.random.rand(10) * 0.1,
    }
    return data

@pytest.fixture
def mock_existing_results():
    """Fixture to provide mock existing results (delta_r2, diagnostics)."""
    return {
        "delta_r2": {
            "delta_r2_value": 0.05,
            "reduced_model_r2": 0.07,
            "full_model_r2": 0.12,
        },
        "diagnostics": {
            "VIF": {
                "Global_Signal_SD": 2.1,
                "Mean_FD": 1.5,
                "Mean_DVARS": 1.8,
                "Age": 1.2,
                "Sex": 1.1,
            },
            "correlation_matrix": {
                "Global_Signal_SD_Mean_FD": 0.15,
            },
        },
    }

def test_compute_null_distribution_stats(mock_null_results, mock_modeling_results):
    """Test that null distribution stats and p-value are computed correctly."""
    from model_report import compute_null_distribution_stats

    null_maes = mock_null_results["null_maes"]
    observed_mae = mock_modeling_results["mean_mae"]

    stats = compute_null_distribution_stats(null_maes, observed_mae)

    assert "mean_null_mae" in stats
    assert "std_null_mae" in stats
    assert "min_null_mae" in stats
    assert "max_null_mae" in stats
    assert "empirical_p_value" in stats

    # Verify p-value calculation
    expected_p_value = float(np.sum(null_maes <= observed_mae) / len(null_maes))
    assert np.isclose(stats["empirical_p_value"], expected_p_value)

@patch("model_report.load_cleaned_data")
@patch("model_report.run_ridge_regression_with_nested_cv")
@patch("model_report.run_null_distribution_analysis")
@patch("model_report.load_existing_results")
@patch("model_report.write_json")
def test_generate_model_report(
    mock_write_json,
    mock_load_existing,
    mock_null_analysis,
    mock_ridge_cv,
    mock_load_data,
    mock_modeling_results,
    mock_null_results,
    mock_df,
    mock_existing_results,
):
    """Test that generate_model_report produces the correct structure."""
    from model_report import generate_model_report

    # Setup mocks
    mock_load_data.return_value = mock_df
    mock_ridge_cv.return_value = mock_modeling_results
    mock_null_analysis.return_value = mock_null_results
    mock_load_existing.return_value = mock_existing_results

    report = generate_model_report()

    # Verify structure
    assert "primary_model" in report
    assert "null_distribution" in report
    assert "reduced_model_comparison" in report
    assert "collinearity_diagnostics" in report
    assert "metadata" in report

    # Verify primary model keys
    pm = report["primary_model"]
    assert "mean_out_of_fold_mae" in pm
    assert "mean_out_of_fold_pearson_r" in pm
    assert "mean_out_of_fold_r_squared" in pm
    assert "optimal_alpha" in pm

    # Verify null distribution keys
    nd = report["null_distribution"]
    assert "n_permutations" in nd
    assert "mean_null_mae" in nd
    assert "std_null_mae" in nd
    assert "empirical_p_value" in nd

    # Verify values are passed through correctly
    assert pm["mean_out_of_fold_mae"] == mock_modeling_results["mean_mae"]
    assert nd["n_permutations"] == 1000

@patch("model_report.load_cleaned_data")
@patch("model_report.run_ridge_regression_with_nested_cv")
@patch("model_report.run_null_distribution_analysis")
@patch("model_report.load_existing_results")
@patch("model_report.write_json")
@patch("model_report.Path.exists")
@patch("model_report.Path.mkdir")
def test_main_function(
    mock_mkdir,
    mock_path_exists,
    mock_write_json,
    mock_load_existing,
    mock_null_analysis,
    mock_ridge_cv,
    mock_load_data,
    mock_modeling_results,
    mock_null_results,
    mock_df,
    mock_existing_results,
    capsys,
):
    """Test that main() runs end-to-end and prints summary."""
    from model_report import main

    # Setup mocks
    mock_path_exists.return_value = True
    mock_load_data.return_value = mock_df
    mock_ridge_cv.return_value = mock_modeling_results
    mock_null_analysis.return_value = mock_null_results
    mock_load_existing.return_value = mock_existing_results

    main()

    # Verify write_json was called
    assert mock_write_json.called

    # Verify stdout contains expected summary lines
    captured = capsys.readouterr()
    assert "Primary Model MAE:" in captured.out
    assert "Primary Model Pearson r:" in captured.out
    assert "Empirical p-value:" in captured.out