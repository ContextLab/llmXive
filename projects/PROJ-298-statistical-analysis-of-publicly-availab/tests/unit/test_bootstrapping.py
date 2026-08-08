"""
Unit tests for the bootstrapping module (T016).
Tests the Theil-Sen slope calculation and bootstrap confidence intervals.
"""
import sys
import json
import math
from pathlib import Path
import pytest

# Add the code directory to the path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.bootstrapping import (
    theil_sen_slope,
    bootstrap_theil_sen,
    load_trend_results,
    load_processed_data,
    save_confidence_intervals,
    run_bootstrapping_analysis
)

class TestTheilSenSlope:
    """Tests for the Theil-Sen slope estimator."""

    def test_perfect_linear_increase(self):
        """Test with a perfect linear increasing series."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]  # y = 2x
        slope = theil_sen_slope(x, y)
        assert math.isclose(slope, 2.0, abs_tol=1e-6)

    def test_perfect_linear_decrease(self):
        """Test with a perfect linear decreasing series."""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]  # y = -2x + 12
        slope = theil_sen_slope(x, y)
        assert math.isclose(slope, -2.0, abs_tol=1e-6)

    def test_constant_series(self):
        """Test with a constant series (slope should be 0)."""
        x = [1, 2, 3, 4, 5]
        y = [5, 5, 5, 5, 5]
        slope = theil_sen_slope(x, y)
        assert math.isclose(slope, 0.0, abs_tol=1e-6)

    def test_noisy_series(self):
        """Test with a noisy series."""
        x = [1, 2, 3, 4, 5]
        y = [2.1, 3.9, 6.2, 7.8, 10.1]  # Roughly y = 2x
        slope = theil_sen_slope(x, y)
        # Should be close to 2.0
        assert 1.5 < slope < 2.5

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        x = [1]
        y = [2]
        with pytest.raises(ValueError):
            theil_sen_slope(x, y)

class TestBootstrapTheilSen:
    """Tests for the bootstrap confidence interval calculation."""

    def test_bootstrap_reproducibility(self):
        """Test that bootstrap results are reproducible with the same seed."""
        x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        
        slope1, lower1, upper1 = bootstrap_theil_sen(x, y, n_iterations=100, seed=42)
        slope2, lower2, upper2 = bootstrap_theil_sen(x, y, n_iterations=100, seed=42)
        
        assert math.isclose(slope1, slope2)
        assert math.isclose(lower1, lower2)
        assert math.isclose(upper1, upper2)

    def test_bootstrap_ci_bounds(self):
        """Test that CI lower bound is less than upper bound."""
        x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        
        slope, lower, upper = bootstrap_theil_sen(x, y, n_iterations=100, seed=42)
        
        assert lower <= slope <= upper

    def test_bootstrap_with_noise(self):
        """Test bootstrap with noisy data."""
        x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y = [2.1, 3.8, 6.3, 7.9, 10.2, 11.8, 14.1, 15.9, 18.2, 19.8]
        
        slope, lower, upper = bootstrap_theil_sen(x, y, n_iterations=100, seed=42)
        
        # Slope should be positive
        assert slope > 0
        # CI should be reasonable
        assert lower < upper

class TestRunBootstrappingAnalysis:
    """Tests for the full bootstrapping analysis pipeline."""

    def test_run_analysis_structure(self):
        """Test that the analysis produces the expected output structure."""
        # Create mock data
        mock_data = {
            "tags": {
                "python": {
                    "monthly_data": {
                        "2020-01": 100,
                        "2020-02": 105,
                        "2020-03": 110,
                        "2020-04": 115,
                        "2020-05": 120
                    }
                },
                "javascript": {
                    "monthly_data": {
                        "2020-01": 200,
                        "2020-02": 205,
                        "2020-03": 210,
                        "2020-04": 215,
                        "2020-05": 220
                    }
                }
            }
        }
        
        mock_trend_results = {
            "tags": {
                "python": mock_data["tags"]["python"],
                "javascript": mock_data["tags"]["javascript"]
            }
        }
        
        results = run_bootstrapping_analysis(mock_data, mock_trend_results, n_iterations=50, seed=42)
        
        assert "metadata" in results
        assert "tags" in results
        assert "python" in results["tags"]
        assert "javascript" in results["tags"]
        
        # Check that results contain expected keys
        for tag in ["python", "javascript"]:
            tag_result = results["tags"][tag]
            assert "slope_estimate" in tag_result
            assert "ci_lower" in tag_result
            assert "ci_upper" in tag_result
            assert "n_iterations_used" in tag_result
            assert "n_months" in tag_result

    def test_run_analysis_with_insufficient_data(self):
        """Test that the analysis handles tags with insufficient data gracefully."""
        mock_data = {
            "tags": {
                "small_tag": {
                    "monthly_data": {
                        "2020-01": 10
                    }
                }
            }
        }
        
        mock_trend_results = {
            "tags": mock_data["tags"]
        }
        
        # Should not raise an error, just skip the tag
        results = run_bootstrapping_analysis(mock_data, mock_trend_results, n_iterations=50, seed=42)
        
        # The tag should be skipped or have an error
        assert "small_tag" not in results["tags"] or "error" in results["tags"]["small_tag"]

class TestSaveAndLoad:
    """Tests for save and load functions."""

    def test_save_and_load_confidence_intervals(self, tmp_path):
        """Test saving and loading confidence interval results."""
        test_results = {
            "metadata": {"n_iterations": 100},
            "tags": {
                "test_tag": {
                    "slope_estimate": 1.5,
                    "ci_lower": 1.2,
                    "ci_upper": 1.8
                }
            }
        }
        
        output_file = tmp_path / "test_confidence_interval.json"
        save_confidence_intervals(test_results, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == test_results

if __name__ == "__main__":
    pytest.main([__file__, "-v"])