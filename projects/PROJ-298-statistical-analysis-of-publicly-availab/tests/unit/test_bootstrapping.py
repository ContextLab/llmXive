import json
import math
import numpy as np
from pathlib import Path
import pytest

# Import functions to test
from analysis.bootstrapping import (
    theil_sen_slope,
    block_bootstrap_sample,
    bootstrap_theil_sen,
    run_bootstrapping_analysis,
    load_processed_data,
    load_trend_results,
    save_confidence_intervals
)

class TestTheilSenSlope:
    def test_linear_trend_positive(self):
        """Test Theil-Sen slope with a perfect positive linear trend."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        slope = theil_sen_slope(x, y)
        assert math.isclose(slope, 2.0, rel_tol=1e-6)

    def test_linear_trend_negative(self):
        """Test Theil-Sen slope with a perfect negative linear trend."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        slope = theil_sen_slope(x, y)
        assert math.isclose(slope, -2.0, rel_tol=1e-6)

    def test_no_trend(self):
        """Test Theil-Sen slope with no trend (constant values)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 5, 5, 5, 5])
        slope = theil_sen_slope(x, y)
        assert math.isclose(slope, 0.0, rel_tol=1e-6)

    def test_single_pair(self):
        """Test Theil-Sen slope with minimal data."""
        x = np.array([1, 2])
        y = np.array([1, 3])
        slope = theil_sen_slope(x, y)
        assert math.isclose(slope, 2.0, rel_tol=1e-6)

class TestBlockBootstrap:
    def test_block_bootstrap_preserves_length(self):
        """Test that bootstrap sample has same length as input."""
        time_series = np.random.rand(100)
        block_length = 12
        rng = np.random.default_rng(42)
        
        sample = block_bootstrap_sample(time_series, block_length, rng)
        assert len(sample) == len(time_series)

    def test_block_bootstrap_with_small_series(self):
        """Test block bootstrap with series equal to block length."""
        time_series = np.random.rand(12)
        block_length = 12
        rng = np.random.default_rng(42)
        
        sample = block_bootstrap_sample(time_series, block_length, rng)
        assert len(sample) == 12

    def test_block_bootstrap_too_short(self):
        """Test that block bootstrap raises error for series shorter than block."""
        time_series = np.random.rand(5)
        block_length = 12
        rng = np.random.default_rng(42)
        
        with pytest.raises(ValueError):
            block_bootstrap_sample(time_series, block_length, rng)

class TestBootstrapTheilSen:
    def test_bootstrap_returns_confidence_interval(self):
        """Test that bootstrap returns valid confidence intervals."""
        # Create a simple time series with a known trend
        n = 24
        x = np.arange(n)
        y = 2 * x + np.random.normal(0, 1, n)
        
        median_slope, lower_ci, upper_ci = bootstrap_theil_sen(y, n_iterations=100, random_seed=42)
        
        assert isinstance(median_slope, float)
        assert isinstance(lower_ci, float)
        assert isinstance(upper_ci, float)
        assert lower_ci <= median_slope <= upper_ci

    def test_bootstrap_reproducibility(self):
        """Test that bootstrap results are reproducible with same seed."""
        n = 24
        y = np.random.rand(n) * 10 + np.arange(n) * 2
        
        slope1, lower1, upper1 = bootstrap_theil_sen(y, n_iterations=100, random_seed=42)
        slope2, lower2, upper2 = bootstrap_theil_sen(y, n_iterations=100, random_seed=42)
        
        assert math.isclose(slope1, slope2, rel_tol=1e-10)
        assert math.isclose(lower1, lower2, rel_tol=1e-10)
        assert math.isclose(upper1, upper2, rel_tol=1e-10)

class TestRunBootstrappingAnalysis:
    def test_analysis_with_valid_data(self, tmp_path):
        """Test full analysis pipeline with valid mock data."""
        # Create mock data
        mock_data = {
            "tags": {
                "python": {
                    "monthly_frequencies": [10, 12, 15, 18, 20, 22, 25, 28, 30, 32, 35, 38, 40]
                },
                "javascript": {
                    "monthly_frequencies": [20, 22, 25, 28, 30, 32, 35, 38, 40, 42, 45, 48, 50]
                }
            }
        }
        
        mock_trend_results = {
            "tags": [
                {"tag": "python"},
                {"tag": "javascript"}
            ]
        }
        
        # Run analysis
        results = run_bootstrapping_analysis(mock_data, mock_trend_results)
        
        # Verify structure
        assert "metadata" in results
        assert "tag_results" in results
        assert "python" in results["tag_results"]
        assert "javascript" in results["tag_results"]
        
        # Verify results have expected fields
        for tag in ["python", "javascript"]:
            tag_result = results["tag_results"][tag]
            assert "status" in tag_result
            assert tag_result["status"] == "success"
            assert "theil_sen_slope" in tag_result
            assert "confidence_interval" in tag_result
            assert "lower" in tag_result["confidence_interval"]
            assert "upper" in tag_result["confidence_interval"]

    def test_analysis_with_insufficient_data(self, tmp_path):
        """Test analysis with time series shorter than block length."""
        mock_data = {
            "tags": {
                "short_tag": {
                    "monthly_frequencies": [1, 2, 3, 4, 5]  # Only 5 points, block length is 12
                }
            }
        }
        
        mock_trend_results = {
            "tags": [
                {"tag": "short_tag"}
            ]
        }
        
        results = run_bootstrapping_analysis(mock_data, mock_trend_results)
        
        assert results["tag_results"]["short_tag"]["status"] == "insufficient_data"
        assert "reason" in results["tag_results"]["short_tag"]

class TestSaveConfidenceIntervals:
    def test_save_and_load(self, tmp_path):
        """Test that results can be saved and loaded correctly."""
        output_file = tmp_path / "test_confidence_interval.json"
        
        test_results = {
            "metadata": {"test": "value"},
            "tag_results": {
                "test_tag": {
                    "theil_sen_slope": 1.5,
                    "confidence_interval": {"lower": 1.0, "upper": 2.0}
                }
            }
        }
        
        save_confidence_intervals(test_results, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == test_results