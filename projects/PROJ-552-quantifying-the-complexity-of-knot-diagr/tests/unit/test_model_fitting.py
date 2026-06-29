"""Unit tests for model_fitting module."""

import json
import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from analysis.model_fitting import (
    RegressionMetrics,
    fit_linear_model,
    fit_logarithmic_model,
    fit_polynomial_model,
    identify_residual_families,
    write_regression_metrics_report,
    write_residual_analysis_report,
)


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        "knot_id": [f"K{i}" for i in range(1, 11)],
        "crossing_number": [3, 4, 5, 5, 6, 6, 7, 7, 8, 8],
        "braid_index": [2, 3, 3, 4, 4, 5, 4, 5, 5, 6],
        "hyperbolic_volume": [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
        "alternating": [True, True, False, False, False, False, False, False, False, False],
    }
    return pd.DataFrame(data)


def test_fit_linear_model(sample_df):
    """Test linear model fitting."""
    result = fit_linear_model(
        sample_df,
        features=["crossing_number", "braid_index"],
        target="hyperbolic_volume"
    )

    assert result.metrics is not None
    assert isinstance(result.metrics, RegressionMetrics)
    assert result.metrics.model_type == "linear"
    assert 0 <= result.metrics.r_squared <= 1
    assert result.metrics.mae >= 0
    assert "crossing_number" in result.metrics.coefficients
    assert "braid_index" in result.metrics.coefficients
    assert len(result.residuals) == len(sample_df)


def test_fit_polynomial_model(sample_df):
    """Test polynomial model fitting."""
    result = fit_polynomial_model(
        sample_df,
        feature="crossing_number",
        degree=2,
        target="hyperbolic_volume"
    )

    assert result.metrics is not None
    assert "polynomial_degree_2" in result.metrics.model_type
    assert 0 <= result.metrics.r_squared <= 1
    assert result.metrics.mae >= 0


def test_fit_logarithmic_model(sample_df):
    """Test logarithmic model fitting."""
    # Filter to positive crossing numbers
    df_pos = sample_df[sample_df["crossing_number"] > 0].copy()
    result = fit_logarithmic_model(
        df_pos,
        feature="crossing_number",
        target="hyperbolic_volume"
    )

    assert result.metrics is not None
    assert result.metrics.model_type == "logarithmic"
    assert 0 <= result.metrics.r_squared <= 1


def test_identify_residual_families(sample_df):
    """Test residual family identification."""
    result = fit_linear_model(
        sample_df,
        features=["crossing_number"],
        target="hyperbolic_volume"
    )

    outliers, family_counts = identify_residual_families(sample_df, result, threshold_std=1.5)

    assert isinstance(outliers, list)
    assert isinstance(family_counts, dict)
    # At least some entries should be categorized
    assert len(family_counts) > 0


def test_write_regression_metrics_report(tmp_path):
    """Test writing regression metrics report."""
    metrics = [
        RegressionMetrics(
            model_type="linear",
            r_squared=0.95,
            aic=10.0,
            bic=12.0,
            mae=0.5,
            coefficients={"x": 1.0},
            intercept=0.0
        )
    ]

    output_path = tmp_path / "metrics.json"
    write_regression_metrics_report(output_path, metrics)

    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["r_squared"] == 0.95


def test_write_residual_analysis_report(tmp_path):
    """Test writing residual analysis report."""
    from analysis.model_fitting import ResidualEntry

    entries = [
        ResidualEntry(
            knot_id="K1",
            crossing_number=3.0,
            braid_index=2.0,
            hyperbolic_volume=0.5,
            predicted_volume=0.4,
            residual=0.1,
            residual_std=0.05,
            is_outlier=True,
            family="other"
        )
    ]

    family_counts = {"other": 1}

    output_path = tmp_path / "residuals.md"
    write_residual_analysis_report(output_path, entries, family_counts)

    assert output_path.exists()
    content = output_path.read_text()
    assert "Residual Analysis Report" in content
    assert "K1" in content
    assert "other" in content


def test_fit_linear_model_no_data():
    """Test linear model with no data."""
    df = pd.DataFrame({
        "x": [],
        "y": []
    })
    with pytest.raises(ValueError):
        fit_linear_model(df, features=["x"], target="y")


def test_fit_logarithmic_model_no_positive():
    """Test logarithmic model with no positive values."""
    df = pd.DataFrame({
        "x": [-1, -2, 0],
        "y": [1, 2, 3]
    })
    with pytest.raises(ValueError):
        fit_logarithmic_model(df, feature="x", target="y")