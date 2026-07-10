"""
Unit tests for correlation analysis logic (T027).

Tests cover:
1. Spearman correlation calculation (math verification).
2. Iterative permutation test logic (convergence and stability).
3. Edge cases (constant data, insufficient samples).

These tests verify the mathematical correctness of functions in 
code/analysis/correlation.py without requiring real external data.
"""
import pytest
import numpy as np
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.correlation import (
    calculate_spearman_correlation,
    run_iterative_permutation_test,
    filter_by_condition
)


class TestSpearmanCorrelation:
    """Tests for calculate_spearman_correlation."""

    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data (rho should be 1.0)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        rho, p_value = calculate_spearman_correlation(x, y)
        
        assert np.isclose(rho, 1.0, atol=1e-5), f"Expected rho=1.0, got {rho}"
        assert p_value == 0.0, f"Expected p=0.0 for perfect correlation, got {p_value}"

    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data (rho should be -1.0)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        
        rho, p_value = calculate_spearman_correlation(x, y)
        
        assert np.isclose(rho, -1.0, atol=1e-5), f"Expected rho=-1.0, got {rho}"
        assert p_value == 0.0, f"Expected p=0.0 for perfect negative correlation, got {p_value}"

    def test_no_correlation(self):
        """Test with uncorrelated data (rho should be near 0)."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        rho, p_value = calculate_spearman_correlation(x, y)
        
        # With random data, rho should be small (not exactly 0 due to sampling)
        assert abs(rho) < 0.2, f"Expected |rho| < 0.2 for random data, got {rho}"
        assert p_value > 0.05, f"Expected p > 0.05 for random data, got {p_value}"

    def test_constant_data(self):
        """Test behavior with constant data (should handle gracefully)."""
        x = np.array([5, 5, 5, 5, 5])
        y = np.array([1, 2, 3, 4, 5])
        
        # Should not raise an exception
        rho, p_value = calculate_spearman_correlation(x, y)
        
        # Spearman correlation is undefined for constant data, 
        # but implementation should return NaN or 0 without crashing
        assert np.isnan(rho) or np.isclose(rho, 0.0), \
            f"Expected NaN or 0 for constant data, got {rho}"

    def test_insufficient_samples(self):
        """Test with insufficient samples (< 3 points)."""
        x = np.array([1, 2])
        y = np.array([3, 4])
        
        # Should handle gracefully
        rho, p_value = calculate_spearman_correlation(x, y)
        
        # With only 2 points, correlation is mathematically 1 or -1 but p-value is undefined
        # Implementation should return valid numbers or NaN
        assert isinstance(rho, (float, np.floating))
        assert isinstance(p_value, (float, np.floating))


class TestIterativePermutationTest:
    """Tests for run_iterative_permutation_test."""

    def test_convergence_detection(self):
        """Test that the permutation test converges when p-value stabilizes."""
        np.random.seed(42)
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = np.array([2, 4, 6, 8, 10, 12, 14, 16, 18, 20])
        
        # Use small iterations for testing
        result = run_iterative_permutation_test(
            x, y, 
            initial_iterations=100, 
            stability_window=5, 
            stability_threshold=0.001, 
            max_iterations=500
        )
        
        assert "rho" in result, "Result should contain 'rho'"
        assert "p_value" in result, "Result should contain 'p_value'"
        assert "iterations" in result, "Result should contain 'iterations'"
        assert "converged" in result, "Result should contain 'converged'"
        
        # For perfectly correlated data, p-value should be very small
        assert result["p_value"] < 0.05, f"Expected p < 0.05 for perfect correlation, got {result['p_value']}"

    def test_stability_check_logic(self):
        """Test that p-value variance is calculated correctly over the window."""
        # This is a logic test - we verify the function runs without error
        # and produces a result with the expected structure
        np.random.seed(123)
        x = np.random.randn(50)
        y = np.random.randn(50)
        
        result = run_iterative_permutation_test(
            x, y,
            initial_iterations=50,
            stability_window=3,
            stability_threshold=0.01,
            max_iterations=200
        )
        
        assert result["iterations"] <= 200, "Should not exceed max_iterations"
        assert 0.0 <= result["p_value"] <= 1.0, "p-value should be in [0, 1]"

    def test_max_iterations_cap(self):
        """Test that the function stops at max_iterations even if not converged."""
        np.random.seed(999)
        x = np.random.randn(30)
        y = np.random.randn(30)
        
        result = run_iterative_permutation_test(
            x, y,
            initial_iterations=10,
            stability_window=2,
            stability_threshold=0.0001,  # Very strict to prevent convergence
            max_iterations=50
        )
        
        assert result["iterations"] == 50, "Should hit max_iterations"
        assert result.get("convergence_warning", False) or not result.get("converged", True), \
            "Should warn or indicate non-convergence"

    def test_input_validation(self):
        """Test handling of mismatched array lengths."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        
        with pytest.raises(ValueError):
            run_iterative_permutation_test(x, y)


class TestFilterByCondition:
    """Tests for filter_by_condition helper."""

    def test_filter_by_condition_value(self):
        """Test filtering data by a specific condition value."""
        # Simulate a variance matrix structure with metadata
        data = {
            "data": {
                "gene1": {"var_epigenetic": 0.5, "var_expression": 0.3, "condition": "fluctuating"},
                "gene2": {"var_epigenetic": 0.2, "var_expression": 0.4, "condition": "constant"},
                "gene3": {"var_epigenetic": 0.6, "var_expression": 0.7, "condition": "fluctuating"},
                "gene4": {"var_epigenetic": 0.1, "var_expression": 0.2, "condition": "constant"},
            }
        }
        
        filtered = filter_by_condition(data, "fluctuating")
        
        assert len(filtered) == 2, f"Expected 2 genes, got {len(filtered)}"
        assert "gene1" in filtered
        assert "gene3" in filtered
        assert "gene2" not in filtered
        assert "gene4" not in filtered

    def test_filter_by_nonexistent_condition(self):
        """Test filtering by a condition that doesn't exist."""
        data = {
            "data": {
                "gene1": {"var_epigenetic": 0.5, "var_expression": 0.3, "condition": "fluctuating"},
            }
        }
        
        filtered = filter_by_condition(data, "nonexistent")
        
        assert len(filtered) == 0, "Should return empty list for non-existent condition"

    def test_filter_with_missing_metadata(self):
        """Test filtering when some genes are missing condition metadata."""
        data = {
            "data": {
                "gene1": {"var_epigenetic": 0.5, "var_expression": 0.3, "condition": "fluctuating"},
                "gene2": {"var_epigenetic": 0.2, "var_expression": 0.4},  # Missing condition
                "gene3": {"var_epigenetic": 0.6, "var_expression": 0.7, "condition": "fluctuating"},
            }
        }
        
        filtered = filter_by_condition(data, "fluctuating")
        
        # Should include only genes with matching condition
        assert len(filtered) == 2, f"Expected 2 genes, got {len(filtered)}"
        assert "gene1" in filtered
        assert "gene3" in filtered


class TestIntegrationScenarios:
    """Integration-style tests for realistic scenarios."""

    def test_full_correlation_workflow(self):
        """Simulate a full correlation analysis workflow on synthetic data."""
        np.random.seed(42)
        
        # Generate synthetic data with known correlation
        n_genes = 100
        base_epigenetic = np.random.randn(n_genes)
        # Add a linear relationship with noise
        base_expression = 0.8 * base_epigenetic + np.random.randn(n_genes) * 0.2
        
        x = base_epigenetic
        y = base_expression
        
        # Calculate correlation
        rho, p_value = calculate_spearman_correlation(x, y)
        
        # Verify positive correlation
        assert rho > 0.5, f"Expected rho > 0.5, got {rho}"
        assert p_value < 0.05, f"Expected p < 0.05, got {p_value}"
        
        # Run permutation test
        perm_result = run_iterative_permutation_test(
            x, y,
            initial_iterations=50,
            stability_window=5,
            stability_threshold=0.01,
            max_iterations=200
        )
        
        # Permutation p-value should also be significant
        assert perm_result["p_value"] < 0.1, f"Expected perm p < 0.1, got {perm_result['p_value']}"
        assert perm_result["rho"] == rho, "Permutation test rho should match direct calculation"

    def test_edge_case_small_dataset(self):
        """Test with a very small dataset (minimum viable for correlation)."""
        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([1.1, 2.2, 2.9, 4.1])
        
        rho, p_value = calculate_spearman_correlation(x, y)
        
        # Should produce valid results
        assert -1.0 <= rho <= 1.0, "rho must be in [-1, 1]"
        assert 0.0 <= p_value <= 1.0, "p-value must be in [0, 1]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])