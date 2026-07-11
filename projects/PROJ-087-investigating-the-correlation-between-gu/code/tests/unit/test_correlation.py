"""
Unit tests for correlation analysis module (US2).
Tests Spearman correlation calculation and Benjamini-Hochberg correction.
"""
import pytest
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

from src.correlation import (
    calculate_spearman_correlation,
    apply_benjamini_hochberg,
    flag_correlations
)


@pytest.fixture
def sample_diversity_df():
    """Create a sample DataFrame with diversity and sleep metrics."""
    np.random.seed(42)
    n = 100
    data = {
        "sample_id": [f"S{i}" for i in range(n)],
        "shannon_diversity": np.random.normal(3.5, 0.5, n),
        "simpson_diversity": np.random.normal(0.8, 0.1, n),
        "observed_otus": np.random.normal(200, 30, n),
        "sleep_efficiency": np.random.normal(85, 10, n),
        "sleep_duration_hours": np.random.normal(7, 1.5, n),
        "wake_after_sleep_onset": np.random.normal(20, 10, n)
    }
    # Introduce a known correlation for testing
    data["sleep_efficiency"] = data["shannon_diversity"] * 10 + np.random.normal(0, 2, n)
    return pd.DataFrame(data)


def test_spearman_correlation_calculation(sample_diversity_df):
    """
    Test that Spearman correlation is calculated correctly.
    We expect a positive correlation between shannon_diversity and sleep_efficiency
    because we engineered it in the fixture.
    """
    diversity_cols = ["shannon_diversity", "simpson_diversity"]
    sleep_cols = ["sleep_efficiency"]

    result_df = calculate_spearman_correlation(
        sample_diversity_df,
        sleep_metrics=sleep_cols,
        diversity_metrics=diversity_cols
    )

    assert not result_df.empty, "Result DataFrame should not be empty"
    assert "r" in result_df.columns
    assert "p" in result_df.columns
    assert "is_moderate" in result_df.columns

    # Check specific correlation for engineered relationship
    shannon_sleep = result_df[
        (result_df["metric_diversity"] == "shannon_diversity") &
        (result_df["metric_sleep"] == "sleep_efficiency")
    ]

    assert not shannon_sleep.empty, "Shannon vs Sleep Efficiency correlation missing"
    r_val = shannon_sleep["r"].values[0]

    # Verify magnitude and sign (positive correlation)
    assert r_val > 0.5, f"Expected strong positive correlation, got {r_val}"

    # Verify p-value is small for this strong correlation
    p_val = shannon_sleep["p"].values[0]
    assert p_val < 0.05, f"Expected significant p-value, got {p_val}"


def test_benjamini_hochberg_correction():
    """
    Test Benjamini-Hochberg correction logic.
    Creates a known set of p-values and verifies the monotonicity of adjusted p-values.
    """
    # Create a DataFrame with known p-values
    df = pd.DataFrame({
        "p": [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
    })

    result_df = apply_benjamini_hochberg(df, p_col="p", q_col="q")

    assert "q" in result_df.columns
    assert len(result_df) == len(df)

    # Check monotonicity: adjusted p-values should be non-decreasing when sorted by raw p
    sorted_q = result_df.sort_values("p")["q"]
    assert all(sorted_q.diff().fillna(0) >= -1e-9), "Adjusted p-values must be non-decreasing"

    # Check that q-values are <= 1
    assert all(result_df["q"] <= 1.0), "Adjusted p-values must be <= 1.0"

    # Check that q-values are >= raw p-values (property of BH)
    assert all(result_df["q"] >= result_df["p"] - 1e-9), "Adjusted p-values should be >= raw p-values"


def test_flag_correlations():
    """Test the flagging logic for moderate and meaningful correlations."""
    df = pd.DataFrame({
        "r": [0.1, 0.35, -0.4, 0.29, 0.5],
        "p": [0.5, 0.01, 0.02, 0.04, 0.06],
        "q": [0.6, 0.03, 0.04, 0.05, 0.09]
    })

    result_df = flag_correlations(df, r_threshold=0.3, q_threshold=0.05)

    assert "is_moderate" in result_df.columns
    assert "is_meaningful" in result_df.columns

    # Check is_moderate logic (|r| > 0.3)
    expected_moderate = [False, True, True, False, True]
    assert list(result_df["is_moderate"]) == expected_moderate

    # Check is_meaningful logic (q < 0.05 AND |r| > 0.3)
    expected_meaningful = [False, True, True, False, False]
    assert list(result_df["is_meaningful"]) == expected_meaningful


def test_empty_dataframe_handling():
    """Test that functions handle empty DataFrames gracefully."""
    empty_df = pd.DataFrame(columns=["sample_id", "shannon_diversity", "sleep_efficiency"])

    result = calculate_spearman_correlation(
        empty_df,
        sleep_metrics=["sleep_efficiency"],
        diversity_metrics=["shannon_diversity"]
    )

    assert result.empty
    assert "metric_diversity" in result.columns

    # Test BH on empty
    bh_result = apply_benjamini_hochberg(result)
    assert bh_result.empty

    # Test flagging on empty
    flag_result = flag_correlations(bh_result)
    assert flag_result.empty
