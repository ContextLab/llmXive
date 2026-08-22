"""
Unit tests for the recalibration module.

Tests cover:
- Configuration loading
- Nonconformity score computation
- Adaptive weight calculation
- Recalibration application
- Full ACP pipeline integration
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from metrics import empirical_coverage
from recalibration import (
    apply_recalibration,
    compute_adaptive_weight,
    compute_nonconformity_scores,
    load_config,
    process_multiple_series,
    run_acp_calibration,
    save_recalibration_params,
)


@pytest.fixture
def sample_config():
    """Create a temporary config file for testing."""
    config_data = {
        "nominal_levels": [0.80, 0.95],
        "aci_alpha": 0.05,
        "threshold": 0.02,
        "seed": 42,
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    yield config_path

    # Cleanup
    if os.path.exists(config_path):
        os.remove(config_path)


@pytest.fixture
def sample_series_data():
    """Generate sample time series data for testing."""
    np.random.seed(42)
    n_points = 100

    # True values with some noise
    y_true = np.random.randn(n_points) + np.linspace(0, 1, n_points)

    # Predictions with some under-coverage (intervals too narrow)
    y_pred_lower = y_true - 0.5 + np.random.randn(n_points) * 0.1
    y_pred_upper = y_true + 0.5 + np.random.randn(n_points) * 0.1

    return {
        "series_id": "test_series_001",
        "y_true": y_true,
        "y_pred_lower": y_pred_lower,
        "y_pred_upper": y_pred_upper,
    }


def test_load_config_success(sample_config):
    """Test successful configuration loading."""
    config = load_config(sample_config)

    assert "nominal_levels" in config
    assert "aci_alpha" in config
    assert config["nominal_levels"] == [0.80, 0.95]
    assert config["aci_alpha"] == 0.05


def test_load_config_missing_file():
    """Test loading a non-existent config file."""
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_file.yaml")


def test_compute_nonconformity_scores_all_inside():
    """Test scores when all points are inside the interval."""
    y_true = np.array([0.0, 1.0, 2.0])
    y_pred_lower = np.array([-1.0, 0.0, 1.0])
    y_pred_upper = np.array([1.0, 2.0, 3.0])

    scores = compute_nonconformity_scores(y_true, y_pred_lower, y_pred_upper)

    # All points inside, so scores should be 0
    assert np.all(scores == 0.0)


def test_compute_nonconformity_scores_some_outside():
    """Test scores when some points are outside the interval."""
    y_true = np.array([0.0, 5.0, 2.0])  # 5.0 is above upper bound
    y_pred_lower = np.array([-1.0, 0.0, 1.0])
    y_pred_upper = np.array([1.0, 2.0, 3.0])

    scores = compute_nonconformity_scores(y_true, y_pred_lower, y_pred_upper)

    # First point: inside -> 0
    # Second point: outside (5 - 2 = 3)
    # Third point: inside -> 0
    assert scores[0] == 0.0
    assert scores[1] == 3.0
    assert scores[2] == 0.0


def test_compute_adaptive_weight_empty_scores():
    """Test adaptive weight with empty scores."""
    scores = np.array([])
    weight = compute_adaptive_weight(scores, 0.95)

    assert weight == 1.0


def test_compute_adaptive_weight_normal_case():
    """Test adaptive weight calculation with normal data."""
    np.random.seed(42)
    scores = np.random.randn(100) * 0.5

    weight = compute_adaptive_weight(scores, 0.95, alpha=0.05)

    # Weight should be in reasonable range
    assert 0.5 <= weight <= 2.0


def test_apply_recalibration_basic():
    """Test basic recalibration application."""
    y_pred_lower = np.array([0.0, 1.0, 2.0])
    y_pred_upper = np.array([2.0, 3.0, 4.0])
    weight = 1.2  # Slight expansion

    rec_lower, rec_upper, metadata = apply_recalibration(
        y_pred_lower, y_pred_upper, weight
    )

    # Intervals should be wider
    original_width = y_pred_upper - y_pred_lower
    rec_width = rec_upper - rec_lower

    assert np.all(rec_width > original_width)
    assert "weight_applied" in metadata


def test_apply_recalibration_with_coverage_check(sample_series_data):
    """Test recalibration with coverage improvement verification."""
    y_true = sample_series_data["y_true"]
    y_pred_lower = sample_series_data["y_pred_lower"]
    y_pred_upper = sample_series_data["y_pred_upper"]

    # Compute initial coverage
    initial_cov = empirical_coverage(y_true, y_pred_lower, y_pred_upper)

    # Compute weight (assuming under-coverage, weight > 1)
    scores = compute_nonconformity_scores(y_true, y_pred_lower, y_pred_upper)
    weight = compute_adaptive_weight(scores, 0.95, alpha=0.05)

    # Apply recalibration
    rec_lower, rec_upper, metadata = apply_recalibration(
        y_pred_lower, y_pred_upper, weight, y_true, 0.95
    )

    # Verify coverage improvement
    rec_cov = empirical_coverage(y_true, rec_lower, rec_upper)

    assert "original_coverage" in metadata
    assert "recalibrated_coverage" in metadata
    assert "coverage_improvement" in metadata

    # Coverage should not decrease significantly (might stay same if already good)
    assert rec_cov >= initial_cov - 0.01  # Allow small numerical tolerance


def test_run_acp_calibration_full_pipeline(sample_series_data):
    """Test the full ACP calibration pipeline."""
    y_true = sample_series_data["y_true"]
    y_pred_lower = sample_series_data["y_pred_lower"]
    y_pred_upper = sample_series_data["y_pred_upper"]

    rec_lower, rec_upper, metadata = run_acp_calibration(
        y_true, y_pred_lower, y_pred_upper, nominal_coverage=0.95
    )

    assert len(rec_lower) == len(y_true)
    assert len(rec_upper) == len(y_true)
    assert "nominal_coverage" in metadata
    assert "weight_applied" in metadata
    assert metadata["nominal_coverage"] == 0.95


def test_save_recalibration_params(sample_config):
    """Test saving recalibration parameters to JSON."""
    params = {
        "nominal_coverage": 0.95,
        "weight_applied": 1.15,
        "improvement": 0.03,
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        output_path = f.name

    try:
        save_recalibration_params(params, output_path)

        # Verify file exists and contains valid JSON
        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            loaded_params = json.load(f)

        assert loaded_params == params
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_process_multiple_series():
    """Test processing multiple time series."""
    np.random.seed(42)
    n_series = 3
    n_points = 50

    series_data = []
    for i in range(n_series):
        y_true = np.random.randn(n_points)
        y_pred_lower = y_true - 0.8 + np.random.randn(n_points) * 0.1
        y_pred_upper = y_true + 0.8 + np.random.randn(n_points) * 0.1

        series_data.append(
            {
                "series_id": f"series_{i}",
                "y_true": y_true,
                "y_pred_lower": y_pred_lower,
                "y_pred_upper": y_pred_upper,
            }
        )

    nominal_levels = [0.80, 0.95]

    results_df = process_multiple_series(series_data, nominal_levels)

    # Verify DataFrame structure
    assert isinstance(results_df, pd.DataFrame)
    assert len(results_df) == n_series * len(nominal_levels)
    assert "series_id" in results_df.columns
    assert "nominal_coverage" in results_df.columns
    assert "improvement" in results_df.columns

    # Verify all series are present
    assert set(results_df["series_id"].unique()) == {
        f"series_{i}" for i in range(n_series)
    }


def test_recalibration_improves_coverage():
    """Test that recalibration generally improves coverage for under-covered intervals."""
    np.random.seed(42)
    n_points = 200

    # Create intentionally under-covered intervals
    y_true = np.random.randn(n_points)
    y_pred_lower = y_true - 0.3  # Too narrow
    y_pred_upper = y_true + 0.3  # Too narrow

    initial_cov = empirical_coverage(y_true, y_pred_lower, y_pred_upper)

    # Apply recalibration
    rec_lower, rec_upper, metadata = run_acp_calibration(
        y_true, y_pred_lower, y_pred_upper, nominal_coverage=0.95
    )

    rec_cov = empirical_coverage(y_true, rec_lower, rec_upper)

    # Recalibrated coverage should be higher (closer to 0.95)
    assert rec_cov >= initial_cov
    assert rec_cov > 0.8  # Should be reasonably close to target