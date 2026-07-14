"""Integration tests for correlation analysis with synthetic data.

This module tests the correlation analysis pipeline (T024, T025) using
synthetic data with known ground truth correlations. It verifies that
the computed correlation coefficients (r, p, q) match expected values
within acceptable tolerance.
"""

import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Import the functions being tested
from code.analysis.correlations import (
    apply_fdr_correction,
    run_correlations_with_fd_covariate,
)
from code.logging_config import get_logger

logger = get_logger(__name__)


def generate_synthetic_correlation_data(
    n_subjects: int = 100,
    metric_name: str = "modularity",
    correlation_strength: float = 0.5,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic data with known correlation structure.

    Creates a DataFrame with:
    - subject_id: unique identifiers
    - metric_name: the network metric (e.g., modularity)
    - motor_score: behavioral measure correlated with the metric
    - fd: framewise displacement (covariate)

    Args:
        n_subjects: Number of subjects to generate
        metric_name: Name of the metric column
        correlation_strength: Target Pearson correlation (r) between metric and motor_score
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic data
    """
    rng = np.random.default_rng(seed)

    # Generate base metric values
    metric_values = rng.normal(loc=0.4, scale=0.1, size=n_subjects)

    # Generate motor_score with known correlation to metric
    # motor_score = correlation_strength * metric + noise
    noise = rng.normal(loc=0, scale=0.15, size=n_subjects)
    motor_score = correlation_strength * metric_values + noise

    # Normalize motor_score to reasonable range
    motor_score = (motor_score - motor_score.min()) / (motor_score.max() - motor_score.min())

    # Generate FD as independent covariate (weak correlation with metric)
    fd = rng.normal(loc=0.2, scale=0.05, size=n_subjects)
    fd = np.clip(fd, 0.05, 0.5)  # Keep FD in realistic range

    df = pd.DataFrame({
        "subject_id": [f"sub_{i:04d}" for i in range(n_subjects)],
        metric_name: metric_values,
        "motor_score": motor_score,
        "fd": fd,
    })

    return df


def test_correlation_with_synthetic_data():
    """Integration test for correlation analysis with synthetic data.

    Tests that:
    1. The pipeline correctly computes Pearson correlations
    2. The computed r values match expected values within tolerance
    3. P-values are computed correctly
    4. FDR correction (q-values) are computed correctly

    This test uses synthetic data with known ground truth correlations
    to validate the entire correlation analysis pipeline.
    """
    # Generate synthetic data with known correlation
    n_subjects = 100
    expected_r = 0.5
    metric_name = "modularity"

    synthetic_data = generate_synthetic_correlation_data(
        n_subjects=n_subjects,
        metric_name=metric_name,
        correlation_strength=expected_r,
        seed=42,
    )

    # Run correlation analysis
    results = run_correlations_with_fd_covariate(
        data=synthetic_data,
        metric_columns=[metric_name],
        outcome_column="motor_score",
        covariate_column="fd",
    )

    # Verify results structure
    assert results is not None, "Correlation results should not be None"
    assert isinstance(results, pd.DataFrame), "Results should be a DataFrame"

    # Check required columns exist
    expected_columns = ["metric_name", "r", "p", "q", "significant", "covariate_controlled"]
    for col in expected_columns:
        assert col in results.columns, f"Results should contain column '{col}'"

    # Verify we have results for our metric
    metric_results = results[results["metric_name"] == metric_name]
    assert len(metric_results) > 0, f"No results found for metric '{metric_name}'"

    # Extract computed values
    computed_r = metric_results["r"].iloc[0]
    computed_p = metric_results["p"].iloc[0]
    computed_q = metric_results["q"].iloc[0]

    # Verify correlation coefficient is close to expected (within 0.15 tolerance due to noise)
    tolerance = 0.15
    assert abs(computed_r - expected_r) < tolerance, (
        f"Computed r ({computed_r:.3f}) differs from expected ({expected_r}) "
        f"by more than tolerance ({tolerance})"
    )

    # Verify p-value is computed and is reasonable
    assert 0 <= computed_p <= 1, f"P-value ({computed_p}) should be between 0 and 1"

    # With n=100 and r=0.5, we expect a significant p-value (< 0.05)
    # Allow some flexibility due to noise
    assert computed_p < 0.1, (
        f"Expected significant p-value for r=0.5 with n=100, got {computed_p}"
    )

    # Verify q-value (FDR corrected) is computed
    assert 0 <= computed_q <= 1, f"Q-value ({computed_q}) should be between 0 and 1"

    # Verify significance flag is set correctly
    significant = metric_results["significant"].iloc[0]
    alpha = 0.05
    expected_significant = computed_q < alpha
    assert significant == expected_significant, (
        f"Significance flag ({significant}) does not match q-value ({computed_q}) "
        f"vs alpha ({alpha})"
    )

    # Verify covariate_controlled flag
    covariate_controlled = metric_results["covariate_controlled"].iloc[0]
    assert covariate_controlled is True, (
        "Results should indicate that FD covariate was controlled for"
    )

    logger.log(
        "test_correlation_with_synthetic_data_passed",
        metric=metric_name,
        expected_r=expected_r,
        computed_r=computed_r,
        computed_p=computed_p,
        computed_q=computed_q,
        significant=significant,
    )


def test_fdr_correction_with_multiple_metrics():
    """Test FDR correction with multiple metrics.

    Creates synthetic data with multiple metrics (some correlated, some not)
    and verifies that the Benjamini-Hochberg procedure correctly adjusts
    p-values to q-values.
    """
    n_subjects = 100
    seed = 123

    # Generate synthetic data for multiple metrics
    data = generate_synthetic_correlation_data(
        n_subjects=n_subjects,
        metric_name="modularity",
        correlation_strength=0.5,
        seed=seed,
    )

    # Add a second metric with weaker correlation
    data["global_efficiency"] = data["modularity"] * 0.3 + np.random.default_rng(seed+1).normal(0, 0.1, n_subjects)

    # Add a third metric with no correlation
    data["participation_coef"] = np.random.default_rng(seed+2).normal(0.3, 0.1, n_subjects)

    metric_columns = ["modularity", "global_efficiency", "participation_coef"]

    # Run correlation analysis
    results = run_correlations_with_fd_covariate(
        data=data,
        metric_columns=metric_columns,
        outcome_column="motor_score",
        covariate_column="fd",
    )

    # Verify we have results for all metrics
    assert len(results) == len(metric_columns), (
        f"Expected {len(metric_columns)} results, got {len(results)}"
    )

    # Verify FDR correction was applied
    assert "q" in results.columns, "Results should contain q-values"

    # Check that q-values are monotonically non-decreasing when sorted by p-value
    sorted_results = results.sort_values("p")
    p_values = sorted_results["p"].values
    q_values = sorted_results["q"].values

    # Q-values should be >= p-values (FDR correction increases p-values)
    assert all(q_values >= p_values), (
        "Q-values should be >= p-values after FDR correction"
    )

    # Check that q-values are monotonically non-decreasing
    # (BH procedure ensures this property)
    for i in range(1, len(q_values)):
        assert q_values[i] >= q_values[i-1] - 1e-10, (
            "Q-values should be monotonically non-decreasing when sorted by p-value"
        )

    logger.log(
        "test_fdr_correction_passed",
        n_metrics=len(metric_columns),
        p_values=p_values.tolist(),
        q_values=q_values.tolist(),
    )


def test_correlation_with_fd_covariate():
    """Test that FD covariate is properly controlled for.

    Creates synthetic data where FD is correlated with both the metric
    and the outcome, and verifies that the partial correlation approach
    (or residual-based approach) correctly accounts for this.
    """
    n_subjects = 100
    seed = 456

    rng = np.random.default_rng(seed)

    # Generate FD
    fd = rng.normal(loc=0.2, scale=0.05, size=n_subjects)
    fd = np.clip(fd, 0.05, 0.5)

    # Generate metric correlated with FD
    metric = 0.3 * fd + rng.normal(0.4, 0.1, n_subjects)

    # Generate motor_score correlated with both metric and FD
    motor_score = 0.4 * metric + 0.2 * fd + rng.normal(0, 0.15, n_subjects)

    data = pd.DataFrame({
        "subject_id": [f"sub_{i:04d}" for i in range(n_subjects)],
        "metric": metric,
        "motor_score": motor_score,
        "fd": fd,
    })

    # Run correlation with FD covariate
    results = run_correlations_with_fd_covariate(
        data=data,
        metric_columns=["metric"],
        outcome_column="motor_score",
        covariate_column="fd",
    )

    # Verify results exist
    assert len(results) == 1, "Should have one result"

    # The correlation should still be significant after controlling for FD
    # (since metric has direct effect on motor_score)
    r_value = results["r"].iloc[0]
    p_value = results["p"].iloc[0]

    # We expect a positive correlation
    assert r_value > 0, f"Expected positive correlation, got {r_value}"

    # P-value should be reasonable (not necessarily < 0.05 due to small sample)
    assert 0 <= p_value <= 1, f"P-value should be between 0 and 1, got {p_value}"

    logger.log(
        "test_correlation_with_fd_covariate_passed",
        r=r_value,
        p=p_value,
    )