"""
Unit tests for statistics utilities.
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.statistics import (
    load_gradient_norms,
    compare_gradient_stability,
    compare_ablation_results,
    calculate_scaling_exponent
)


class TestLoadGradientNorms:
    """Tests for load_gradient_norms function."""
    
    def test_load_valid_file(self, tmp_path):
        """Test loading a valid gradient norms file."""
        test_data = [{"norm": 0.5}, {"norm": 0.6}, {"norm": 0.7}]
        file_path = tmp_path / "gradient_norms.json"
        file_path.write_text(json.dumps(test_data))
        
        result = load_gradient_norms(str(file_path))
        assert result == test_data
    
    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_gradient_norms(str(tmp_path / "nonexistent.json"))


class TestCompareGradientStability:
    """Tests for compare_gradient_stability function."""
    
    def test_stable_distributions(self, tmp_path):
        """Test with similar distributions (should be stable)."""
        # Generate similar normal distributions
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.1, 100).tolist()
        microcircuit = np.random.normal(0.5, 0.1, 100).tolist()
        
        baseline_file = tmp_path / "baseline.json"
        microcircuit_file = tmp_path / "microcircuit.json"
        
        baseline_file.write_text(json.dumps([{"norm": x} for x in baseline]))
        microcircuit_file.write_text(json.dumps([{"norm": x} for x in microcircuit]))
        
        result = compare_gradient_stability(
            str(baseline_file),
            str(microcircuit_file)
        )
        
        assert "ks_statistic" in result
        assert "p_value" in result
        assert "stable" in result
        # Similar distributions should have high p-value
        assert result["p_value"] > 0.05
        assert result["stable"] is True
    
    def test_different_distributions(self, tmp_path):
        """Test with different distributions (should be unstable)."""
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.1, 100).tolist()
        microcircuit = np.random.normal(1.0, 0.3, 100).tolist()
        
        baseline_file = tmp_path / "baseline.json"
        microcircuit_file = tmp_path / "microcircuit.json"
        
        baseline_file.write_text(json.dumps([{"norm": x} for x in baseline]))
        microcircuit_file.write_text(json.dumps([{"norm": x} for x in microcircuit]))
        
        result = compare_gradient_stability(
            str(baseline_file),
            str(microcircuit_file)
        )
        
        assert "ks_statistic" in result
        assert "p_value" in result
        assert "stable" in result
    
    def test_insufficient_data(self, tmp_path):
        """Test with insufficient data points."""
        baseline_file = tmp_path / "baseline.json"
        microcircuit_file = tmp_path / "microcircuit.json"
        
        baseline_file.write_text(json.dumps([{"norm": 0.5}]))
        microcircuit_file.write_text(json.dumps([{"norm": 0.6}]))
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            compare_gradient_stability(
                str(baseline_file),
                str(microcircuit_file)
            )


class TestCompareAblationResults:
    """Tests for compare_ablation_results function."""
    
    def test_full_and_ablated_present(self, tmp_path):
        """Test with full and ablated variants present."""
        test_data = {
            "results": [
                {"variant": "full", "mae": 0.05, "time": 100.0},
                {"variant": "no_recurrence", "mae": 0.08, "time": 90.0},
                {"variant": "no_inhibition", "mae": 0.07, "time": 95.0},
                {"variant": "no_homeostasis", "mae": 0.09, "time": 105.0}
            ]
        }
        
        input_file = tmp_path / "ablation_results.json"
        output_file = tmp_path / "ablation_stats.json"
        
        input_file.write_text(json.dumps(test_data))
        
        result = compare_ablation_results(str(input_file), str(output_file))
        
        assert "full_mae" in result
        assert "ablated_mae" in result
        assert "mae_diff" in result
        assert "p_value" in result
        assert "significant" in result
        
        assert result["full_mae"] == 0.05
        assert result["ablated_mae"] > 0.05  # Average of ablated should be higher
        assert result["mae_diff"] < 0  # full - ablated should be negative
        
        # Check output file was created
        assert output_file.exists()
    
    def test_missing_full_variant(self, tmp_path):
        """Test with missing full variant."""
        test_data = {
            "results": [
                {"variant": "no_recurrence", "mae": 0.08, "time": 90.0}
            ]
        }
        
        input_file = tmp_path / "ablation_results.json"
        output_file = tmp_path / "ablation_stats.json"
        
        input_file.write_text(json.dumps(test_data))
        
        with pytest.raises(ValueError, match="No 'full' variant found"):
            compare_ablation_results(str(input_file), str(output_file))
    
    def test_missing_ablated_variants(self, tmp_path):
        """Test with missing ablated variants."""
        test_data = {
            "results": [
                {"variant": "full", "mae": 0.05, "time": 100.0}
            ]
        }
        
        input_file = tmp_path / "ablation_results.json"
        output_file = tmp_path / "ablation_stats.json"
        
        input_file.write_text(json.dumps(test_data))
        
        with pytest.raises(ValueError, match="No ablated variants found"):
            compare_ablation_results(str(input_file), str(output_file))
    
    def test_single_ablated_variant(self, tmp_path):
        """Test with only one ablated variant (cannot compute t-test)."""
        test_data = {
            "results": [
                {"variant": "full", "mae": 0.05, "time": 100.0},
                {"variant": "no_recurrence", "mae": 0.08, "time": 90.0}
            ]
        }
        
        input_file = tmp_path / "ablation_results.json"
        output_file = tmp_path / "ablation_stats.json"
        
        input_file.write_text(json.dumps(test_data))
        
        result = compare_ablation_results(str(input_file), str(output_file))
        
        assert result["p_value"] == 1.0  # Cannot compute t-test
        assert result["significant"] is False


class TestCalculateScalingExponent:
    """Tests for calculate_scaling_exponent function."""
    
    def test_valid_scaling_data(self, tmp_path):
        """Test with valid scaling data (1x, 2x, 4x)."""
        test_data = {
            "variants": [
                {"columns": "1x", "params": 10000, "mae": 0.15, "time": 100.0},
                {"columns": "2x", "params": 20000, "mae": 0.12, "time": 180.0},
                {"columns": "4x", "params": 40000, "mae": 0.10, "time": 350.0}
            ]
        }
        
        input_file = tmp_path / "scaling_results.json"
        output_file = tmp_path / "scaling_exponent.json"
        
        input_file.write_text(json.dumps(test_data))
        
        result = calculate_scaling_exponent(str(input_file), str(output_file))
        
        assert "exponent" in result
        assert "r_squared" in result
        assert "interpretation" in result
        
        # With decreasing MAE as params increase, exponent should be negative
        assert result["exponent"] < 0
        assert result["r_squared"] >= 0
        
        # Check output file was created
        assert output_file.exists()
    
    def test_insufficient_data_points(self, tmp_path):
        """Test with only one data point."""
        test_data = {
            "variants": [
                {"columns": "1x", "params": 10000, "mae": 0.15, "time": 100.0}
            ]
        }
        
        input_file = tmp_path / "scaling_results.json"
        
        input_file.write_text(json.dumps(test_data))
        
        with pytest.raises(ValueError, match="Need at least 2 data points"):
            calculate_scaling_exponent(str(input_file))
    
    def test_missing_params_or_mae(self, tmp_path):
        """Test with missing params or mae values."""
        test_data = {
            "variants": [
                {"columns": "1x", "params": 10000, "mae": 0.15, "time": 100.0},
                {"columns": "2x", "params": 20000, "time": 180.0}  # Missing mae
            ]
        }
        
        input_file = tmp_path / "scaling_results.json"
        
        input_file.write_text(json.dumps(test_data))
        
        with pytest.raises(ValueError, match="Missing params or mae"):
            calculate_scaling_exponent(str(input_file))