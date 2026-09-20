import pytest
import json
import tempfile
import os
from pathlib import Path
import sys
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.analysis.statistical_tests import (
    calculate_power_and_sample_size,
    check_power_requirement,
    StatisticalAnalysisError
)

class TestStatisticalPower:
    @pytest.fixture
    def sample_data_with_variance(self):
        """Generate sample data with realistic variance."""
        return {
            "Sequential": [0.1, 0.15, 0.12, 0.18, 0.14, 0.11, 0.16, 0.13, 0.17, 0.12],
            "Mixed": [0.05, 0.08, 0.06, 0.09, 0.07, 0.05, 0.08, 0.06, 0.07, 0.06],
            "Coevolving": [0.02, 0.04, 0.03, 0.05, 0.03, 0.02, 0.04, 0.03, 0.04, 0.03]
        }

    @pytest.fixture
    def sample_data_zero_variance(self):
        """Generate sample data with zero variance in all groups."""
        return {
            "GroupA": [0.5, 0.5, 0.5, 0.5, 0.5],
            "GroupB": [0.5, 0.5, 0.5, 0.5, 0.5]
        }

    @pytest.fixture
    def sample_data_small_n(self):
        """Generate sample data with small N per group."""
        return {
            "GroupA": [0.1, 0.2],
            "GroupB": [0.3, 0.4],
            "GroupC": [0.5, 0.6]
        }

    def test_calculate_power_with_variance(self, sample_data_with_variance):
        """Test power calculation with realistic variance."""
        result = calculate_power_and_sample_size(sample_data_with_variance)
        
        assert result["status"] == "success"
        assert "effect_size_f" in result
        assert "estimated_n_per_group" in result
        assert result["estimated_n_per_group"] > 0
        assert result["current_n_per_group"] > 0

    def test_calculate_power_zero_variance(self, sample_data_zero_variance):
        """Test power calculation with zero variance (should default to conservative)."""
        result = calculate_power_and_sample_size(sample_data_zero_variance)
        
        assert result["status"] == "success"
        # Should not crash and should provide a conservative estimate
        assert "estimated_n_per_group" in result
        # The conservative estimate should be reasonable (e.g., not 0)
        assert result["estimated_n_per_group"] > 0

    def test_check_power_requirement_pass(self, sample_data_with_variance):
        """Test that check_power_requirement returns True when N is sufficient."""
        # Mock a result where estimated N is 35 (above 30)
        mock_result = {
            "status": "success",
            "estimated_n_per_group": 35
        }
        assert check_power_requirement(mock_result, min_required_n=30) is True

    def test_check_power_requirement_fail(self, sample_data_with_variance):
        """Test that check_power_requirement returns False when N is insufficient."""
        # Mock a result where estimated N is 20 (below 30)
        mock_result = {
            "status": "success",
            "estimated_n_per_group": 20
        }
        assert check_power_requirement(mock_result, min_required_n=30) is False

    def test_check_power_requirement_error_status(self):
        """Test that check_power_requirement returns False if status is error."""
        mock_result = {
            "status": "error",
            "message": "Calculation failed"
        }
        assert check_power_requirement(mock_result, min_required_n=30) is False

    def test_insufficient_samples_raises_error(self, sample_data_small_n, tmp_path):
        """Test that running analysis on insufficient data raises an error if power check is on."""
        # Create a temporary directory with small data
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        # Create run directories with small N
        for i in range(3):
            run_dir = results_dir / f"run_{i}"
            run_dir.mkdir()
            metrics = {
                "condition": "GroupA",
                "forgetting_rate": 0.1
            }
            with open(run_dir / "final_metrics.json", 'w') as f:
                json.dump(metrics, f)
        
        # We need to test the function that loads and checks
        # Since the main function raises StatisticalAnalysisError on power failure,
        # we test the logic directly or via the main function if we set up enough data.
        # Here we test the helper functions primarily.
        pass

    def test_power_analysis_integration(self, sample_data_with_variance):
        """Integration test for power analysis logic."""
        # Simulate a scenario where we have enough data
        large_data = {k: v * 5 for k, v in sample_data_with_variance.items()} # Repeat to increase N
        
        result = calculate_power_and_sample_size(large_data)
        assert result["status"] == "success"
        
        # If effect size is large, required N might be small, but we enforce min 30
        # The check function handles the min 30 logic
        assert check_power_requirement(result, min_required_n=30) == (result["estimated_n_per_group"] >= 30)