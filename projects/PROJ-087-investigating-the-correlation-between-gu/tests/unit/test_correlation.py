import pytest
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from src.correlation import (
    calculate_spearman_correlation,
    apply_benjamini_hochberg,
    flag_correlations,
    handle_no_significant_associations,
)


@pytest.fixture
def sample_diversity_df():
    """Create a deterministic sample dataframe for correlation tests."""
    np.random.seed(42)
    n_samples = 100
    data = {
        "sample_id": [f"sample_{i}" for i in range(n_samples)],
        "shannon_index": np.random.normal(loc=3.5, scale=0.5, size=n_samples),
        "simpson_index": np.random.normal(loc=0.8, scale=0.1, size=n_samples),
        "observed_otus": np.random.normal(loc=150, scale=20, size=n_samples),
        "sleep_efficiency": np.random.normal(loc=85, scale=10, size=n_samples),
        "sleep_duration_hours": np.random.normal(loc=7, scale=1.5, size=n_samples),
    }
    return pd.DataFrame(data)


def test_spearman_correlation_calculation(sample_diversity_df):
    """
    Verify that the Spearman correlation calculation matches scipy's output.
    Uses hardcoded small test data within the test function logic via the fixture.
    """
    # Test Shannon vs Sleep Efficiency
    x = sample_diversity_df["shannon_index"]
    y = sample_diversity_df["sleep_efficiency"]

    # Calculate using our function
    r, p = calculate_spearman_correlation(x, y)

    # Calculate using scipy directly for verification
    r_expected, p_expected = spearmanr(x, y)

    # Assert closeness
    assert np.isclose(r, r_expected, rtol=1e-5), f"r value mismatch: {r} vs {r_expected}"
    assert np.isclose(p, p_expected, rtol=1e-5), f"p value mismatch: {p} vs {p_expected}"


def test_benjamini_hochberg_correction():
    """
    Unit test for Benjamini-Hochberg FDR correction.
    Uses hardcoded p-values to verify the mathematical correctness of the adjustment.
    """
    # Hardcoded test data: 10 p-values sorted in ascending order
    # Expected logic: p_adj[i] = p[i] * n / (i + 1)
    # Then ensure monotonicity (cummin from the end)
    p_values = [0.001, 0.005, 0.01, 0.02, 0.04, 0.06, 0.10, 0.20, 0.50, 0.80]
    n = len(p_values)

    # Run the function
    adjusted_p = apply_benjamini_hochberg(p_values)

    # Manual calculation for verification
    # Step 1: Calculate raw adjusted values
    raw_adj = [p_values[i] * n / (i + 1) for i in range(n)]
    # Step 2: Ensure monotonicity (cumulative min from the end)
    # In Python: iterate backwards, keep min(current, next)
    expected_adj = raw_adj.copy()
    for i in range(n - 2, -1, -1):
        if expected_adj[i] > expected_adj[i + 1]:
            expected_adj[i] = expected_adj[i + 1]

    # Cap at 1.0
    expected_adj = [min(p, 1.0) for p in expected_adj]

    # Assert results match expected
    assert len(adjusted_p) == n, "Output length mismatch"
    for i in range(n):
        assert np.isclose(adjusted_p[i], expected_adj[i], rtol=1e-5), (
            f"Index {i}: {adjusted_p[i]} != {expected_adj[i]}"
        )

    # Additional check: monotonicity must hold in the result
    for i in range(n - 1):
        assert adjusted_p[i] <= adjusted_p[i + 1], (
            f"Monotonicity violation at index {i}: {adjusted_p[i]} > {adjusted_p[i + 1]}"
        )


def test_flag_correlations(sample_diversity_df):
    """Test that flagging logic correctly identifies moderate and meaningful correlations."""
    # Create a dataframe with known correlations
    # We will manually construct a result DF to test the flagging logic
    test_results = pd.DataFrame({
        "variable_x": ["A", "B", "C", "D"],
        "variable_y": ["X", "Y", "Z", "W"],
        "r": [0.1, 0.4, -0.35, 0.6],
        "p": [0.5, 0.04, 0.02, 0.001],
        "q": [0.6, 0.06, 0.03, 0.002],  # Adjusted p-values
    })

    flagged = flag_correlations(test_results)

    # Check is_moderate (|r| > 0.3)
    assert flagged.loc[0, "is_moderate"] is False
    assert flagged.loc[1, "is_moderate"] is True
    assert flagged.loc[2, "is_moderate"] is True
    assert flagged.loc[3, "is_moderate"] is True

    # Check is_meaningful (q < 0.05 AND |r| > 0.3)
    assert flagged.loc[0, "is_meaningful"] is False
    assert flagged.loc[1, "is_meaningful"] is False  # q > 0.05
    assert flagged.loc[2, "is_meaningful"] is True
    assert flagged.loc[3, "is_meaningful"] is True


def test_empty_dataframe_handling():
    """Test that the correlation functions handle empty data gracefully."""
    empty_df = pd.DataFrame(columns=["shannon_index", "sleep_efficiency"])
    
    with pytest.raises((ValueError, IndexError)):
        calculate_spearman_correlation(empty_df["shannon_index"], empty_df["sleep_efficiency"])


def test_handle_no_significant_associations():
    """Test the logic for handling cases with no significant associations."""
    # Simulate a results DF where no correlations are meaningful
    results_df = pd.DataFrame({
        "variable_x": ["A", "B"],
        "variable_y": ["X", "Y"],
        "r": [0.1, 0.2],
        "p": [0.8, 0.7],
        "q": [0.9, 0.8],
        "is_moderate": [False, False],
        "is_meaningful": [False, False],
    })

    status = handle_no_significant_associations(results_df)
    assert status == "no_significant_associations"

    # Test with at least one meaningful
    results_df.loc[0, "is_meaningful"] = True
    status = handle_no_significant_associations(results_df)
    assert status == "significant_associations_found"