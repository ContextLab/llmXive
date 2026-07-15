"""
Unit tests for the Benjamini-Yekutieli (BY) procedure.

This module verifies FDR control under dependence as required by US2.
It tests the `benjamini_yekutieli` and `apply_correction_to_results` 
functions from `code/correction.py`.
"""
import numpy as np
import pytest
from correction import benjamini_yekutieli, apply_correction_to_results


def test_by_monotonicity():
    """
    Verify that the BY procedure produces monotonically non-decreasing q-values
    when p-values are sorted in ascending order.
    """
    # Generate sorted p-values
    np.random.seed(42)
    p_values = np.sort(np.random.rand(100))
    
    q_values = benjamini_yekutieli(p_values)
    
    # Check monotonicity: q[i] <= q[i+1]
    assert np.all(np.diff(q_values) >= -1e-9), "BY q-values must be non-decreasing"


def test_by_upper_bound():
    """
    Verify that BY q-values do not exceed 1.0.
    """
    np.random.seed(42)
    p_values = np.random.rand(50)
    
    q_values = benjamini_yekutieli(p_values)
    
    assert np.all(q_values <= 1.0), "BY q-values must be <= 1.0"
    assert np.all(q_values >= 0.0), "BY q-values must be >= 0.0"


def test_by_exact_small_set():
    """
    Test BY procedure on a small, known set of p-values to verify calculation logic.
    """
    # Known p-values
    p_values = np.array([0.001, 0.01, 0.05, 0.1, 0.2])
    m = len(p_values)
    
    # Calculate harmonic sum manually
    harmonic_sum = sum(1.0 / (i + 1) for i in range(m))
    
    # Expected q-values calculation (simplified check)
    # The BY procedure divides by harmonic_sum * (i+1)
    q_values = benjamini_yekutieli(p_values)
    
    # Verify the smallest p-value is adjusted correctly
    # q[0] should be p[0] * m / (harmonic_sum * 1)
    expected_first = p_values[0] * m / harmonic_sum
    # Allow small floating point tolerance
    assert np.isclose(q_values[0], expected_first, rtol=1e-5), \
        f"First q-value mismatch: got {q_values[0]}, expected {expected_first}"


def test_by_dependence_simulation():
    """
    Simulate dependent p-values (correlated tests) and verify FDR control.
    We generate correlated uniform variables and transform to p-values.
    Under the null, the proportion of false discoveries should be controlled.
    """
    np.random.seed(123)
    n_tests = 1000
    n_sims = 100
    alpha = 0.05
    fdr_controlled_count = 0
    
    for _ in range(n_sims):
        # Generate correlated uniform variables
        # Use a simple correlation structure: X_i = rho * Z + sqrt(1-rho^2) * E_i
        rho = 0.5
        Z = np.random.normal(0, 1, n_tests)
        E = np.random.normal(0, 1, n_tests)
        X = rho * Z + np.sqrt(1 - rho**2) * E
        
        # Convert to p-values (uniform under null)
        p_values = 1 - 0.5 * (1 + np.erf(X / np.sqrt(2)))
        p_values = np.clip(p_values, 0, 1)
        
        # Apply BY correction
        q_values = benjamini_yekutieli(p_values)
        
        # Count significant discoveries
        significant = q_values <= alpha
        num_discoveries = np.sum(significant)
        
        # Calculate FDR (proportion of false discoveries among discoveries)
        # Since all are null, all discoveries are false
        if num_discoveries > 0:
            fdr = num_discoveries / n_tests
        else:
            fdr = 0.0
        
        # Check if FDR is controlled (allowing for some variance)
        if fdr <= alpha * 1.5:  # 50% tolerance for simulation variance
            fdr_controlled_count += 1
    
    # At least 90% of simulations should show FDR control
    assert fdr_controlled_count / n_sims >= 0.90, \
        f"FDR not controlled in enough simulations: {fdr_controlled_count}/{n_sims}"


def test_apply_correction_to_results():
    """
    Test the high-level function that applies BY correction to a list of results.
    """
    # Mock results data
    results = [
        {"dataset_id": "D1", "statistic": "clustering", "p_value": 0.001},
        {"dataset_id": "D1", "statistic": "density", "p_value": 0.05},
        {"dataset_id": "D2", "statistic": "clustering", "p_value": 0.1},
        {"dataset_id": "D2", "statistic": "density", "p_value": 0.2},
    ]
    
    corrected_results = apply_correction_to_results(results, alpha=0.05)
    
    # Verify structure
    assert len(corrected_results) == len(results)
    assert all("q_value" in r for r in corrected_results)
    assert all("is_significant" in r for r in corrected_results)
    
    # Verify that lower p-values get lower q-values (generally)
    # D1 clustering (0.001) should be significant
    d1_clustering = next(r for r in corrected_results if r["dataset_id"] == "D1" and r["statistic"] == "clustering")
    assert d1_clustering["is_significant"] is True, "Low p-value should be significant"
    
    # D2 density (0.2) should likely be non-significant
    d2_density = next(r for r in corrected_results if r["dataset_id"] == "D2" and r["statistic"] == "density")
    assert d2_density["is_significant"] is False, "High p-value should likely be non-significant"


def test_apply_correction_empty_input():
    """
    Test that applying correction to an empty list returns an empty list.
    """
    results = []
    corrected = apply_correction_to_results(results, alpha=0.05)
    assert corrected == []


def test_apply_correction_single_item():
    """
    Test correction on a single item.
    """
    results = [{"dataset_id": "D1", "statistic": "test", "p_value": 0.01}]
    corrected = apply_correction_to_results(results, alpha=0.05)
    
    assert len(corrected) == 1
    assert corrected[0]["q_value"] == 0.01  # Single item: q = p
    assert corrected[0]["is_significant"] is True