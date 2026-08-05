import pytest
import numpy as np
import json
import os
from pathlib import Path
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.bootstrapping import (
    theil_sen_slope,
    bootstrap_theil_sen,
    run_bootstrapping_analysis,
    load_processed_data,
    load_trend_results
)

class TestTheilSenSlope:
    """Unit tests for Theil-Sen slope calculation."""

    def test_linear_trend_positive(self):
        """Test with a perfect positive linear trend."""
        x = np.array([0, 1, 2, 3, 4], dtype=float)
        y = np.array([0, 2, 4, 6, 8], dtype=float)
        
        slope = theil_sen_slope(x, y)
        assert abs(slope - 2.0) < 1e-6, f"Expected slope 2.0, got {slope}"

    def test_linear_trend_negative(self):
        """Test with a perfect negative linear trend."""
        x = np.array([0, 1, 2, 3, 4], dtype=float)
        y = np.array([8, 6, 4, 2, 0], dtype=float)
        
        slope = theil_sen_slope(x, y)
        assert abs(slope - (-2.0)) < 1e-6, f"Expected slope -2.0, got {slope}"

    def test_flat_trend(self):
        """Test with a flat (zero slope) trend."""
        x = np.array([0, 1, 2, 3, 4], dtype=float)
        y = np.array([5, 5, 5, 5, 5], dtype=float)
        
        slope = theil_sen_slope(x, y)
        assert abs(slope) < 1e-6, f"Expected slope ~0, got {slope}"

    def test_with_noise(self):
        """Test with noisy data - slope should be close to true value."""
        np.random.seed(42)
        x = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=float)
        true_slope = 1.5
        y = true_slope * x + np.random.normal(0, 0.5, size=len(x))
        
        slope = theil_sen_slope(x, y)
        # Theil-Sen is robust to noise, should be close to true slope
        assert abs(slope - true_slope) < 0.5, f"Expected slope close to {true_slope}, got {slope}"

    def test_single_pair(self):
        """Test with only two points."""
        x = np.array([0, 1], dtype=float)
        y = np.array([0, 10], dtype=float)
        
        slope = theil_sen_slope(x, y)
        assert abs(slope - 10.0) < 1e-6, f"Expected slope 10.0, got {slope}"

class TestBootstrapTheilSen:
    """Unit tests for bootstrap confidence interval calculation."""

    def test_confidence_interval_contains_true_slope(self):
        """Test that CI contains true slope for a known linear trend."""
        np.random.seed(42)
        x = np.arange(0, 20, dtype=float)
        true_slope = 2.0
        y = true_slope * x + np.random.normal(0, 1, size=len(x))
        
        result = bootstrap_theil_sen(x, y, n_iterations=200, random_seed=42)
        
        # CI should contain the true slope (with high probability)
        assert result["ci_lower"] <= true_slope <= result["ci_upper"], \
            f"True slope {true_slope} not in CI [{result['ci_lower']}, {result['ci_upper']}]"

    def test_ci_width_positive(self):
        """Test that confidence interval width is positive."""
        x = np.arange(0, 10, dtype=float)
        y = np.random.normal(0, 1, size=len(x))
        
        result = bootstrap_theil_sen(x, y, n_iterations=100, random_seed=42)
        assert result["ci_width"] > 0, "CI width should be positive"

    def test_ci_width_decreases_with_more_iterations(self):
        """Test that CI width stabilizes with more iterations."""
        x = np.arange(0, 10, dtype=float)
        y = np.random.normal(0, 1, size=len(x))
        
        result_100 = bootstrap_theil_sen(x, y, n_iterations=100, random_seed=42)
        result_500 = bootstrap_theil_sen(x, y, n_iterations=500, random_seed=42)
        
        # Widths should be similar (not necessarily monotonic, but in same ballpark)
        ratio = result_500["ci_width"] / result_100["ci_width"]
        assert 0.5 < ratio < 2.0, f"CI width ratio {ratio} seems unstable"

    def test_different_confidence_levels(self):
        """Test that higher confidence level gives wider CI."""
        x = np.arange(0, 15, dtype=float)
        y = np.random.normal(0, 1, size=len(x))
        
        result_90 = bootstrap_theil_sen(x, y, n_iterations=200, confidence_level=0.90, random_seed=42)
        result_95 = bootstrap_theil_sen(x, y, n_iterations=200, confidence_level=0.95, random_seed=42)
        result_99 = bootstrap_theil_sen(x, y, n_iterations=200, confidence_level=0.99, random_seed=42)
        
        assert result_90["ci_width"] < result_95["ci_width"], "90% CI should be narrower than 95%"
        assert result_95["ci_width"] < result_99["ci_width"], "95% CI should be narrower than 99%"

    def test_reproducibility(self):
        """Test that same seed gives same results."""
        x = np.arange(0, 10, dtype=float)
        y = np.random.normal(0, 1, size=len(x))
        
        result1 = bootstrap_theil_sen(x, y, n_iterations=100, random_seed=123)
        result2 = bootstrap_theil_sen(x, y, n_iterations=100, random_seed=123)
        
        assert result1["slope"] == result2["slope"], "Results should be identical with same seed"
        assert result1["ci_lower"] == result2["ci_lower"], "CI lower should be identical"
        assert result1["ci_upper"] == result2["ci_upper"], "CI upper should be identical"

class TestRunBootstrappingAnalysis:
    """Integration tests for the full bootstrapping analysis pipeline."""

    def test_empty_input(self):
        """Test with empty trend results."""
        processed_data = {"data": {}}
        trend_results = {}
        
        results = run_bootstrapping_analysis(processed_data, trend_results, n_iterations=10)
        assert len(results) == 0, "Should return empty results for empty input"

    def test_insufficient_data_handling(self):
        """Test handling of tags with insufficient data points."""
        processed_data = {
            "data": {
                "small_tag": {
                    "months": ["2020-01", "2020-02"],
                    "frequencies": [10, 20]
                }
            }
        }
        trend_results = {
            "small_tag": {
                "classification": "Stable",
                "p_value": 0.5
            }
        }
        
        results = run_bootstrapping_analysis(
            processed_data, trend_results, 
            n_iterations=10, 
            min_data_points=5
        )
        
        assert "small_tag" in results
        assert results["small_tag"]["status"] == "insufficient_data"

    def test_successful_analysis(self):
        """Test successful analysis with sufficient data."""
        np.random.seed(42)
        months = [f"2020-{str(i).zfill(2)}" for i in range(1, 13)]
        frequencies = list(np.random.normal(100, 10, size=12))
        
        processed_data = {
            "data": {
                "test_tag": {
                    "months": months,
                    "frequencies": frequencies
                }
            }
        }
        trend_results = {
            "test_tag": {
                "classification": "Growth",
                "p_value": 0.01
            }
        }
        
        results = run_bootstrapping_analysis(
            processed_data, trend_results,
            n_iterations=10,
            min_data_points=5
        )
        
        assert "test_tag" in results
        assert results["test_tag"]["status"] != "insufficient_data"
        assert "slope" in results["test_tag"]
        assert "ci_lower" in results["test_tag"]
        assert "ci_upper" in results["test_tag"]
        assert results["test_tag"]["n_data_points"] == 12