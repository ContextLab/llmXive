import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.run_pilot_sensitivity import run_pilot_analysis

class TestPilotSensitivityAnalysis:
    """Tests for the pilot sensitivity analysis functionality."""

    def test_pilot_runs_successfully(self, tmp_path):
        """Test that the pilot analysis runs and produces a valid JSON file."""
        output_path = str(tmp_path / "test_pilot.json")
        result = run_pilot_analysis(output_path=output_path, num_samples=10)
        
        assert result is not None
        assert "num_samples" in result
        assert result["num_samples"] == 10
        assert "epsilon_values" in result
        assert "run_results" in result
        assert "summary" in result
        
        # Verify file was written
        assert Path(output_path).exists()
        
        # Verify JSON structure
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["num_samples"] == 10
        assert len(loaded["run_results"]) == 10

    def test_pilot_output_contains_expected_metrics(self, tmp_path):
        """Test that the pilot output contains the required metrics."""
        output_path = str(tmp_path / "test_pilot_metrics.json")
        result = run_pilot_analysis(output_path=output_path, num_samples=5)
        
        # Check summary structure
        assert "summary" in result
        for eps_str, stats in result["summary"].items():
            assert "mean_delta_kl" in stats
            assert "std_delta_kl" in stats
            assert "stability_score" in stats
            # Ensure numeric types
            assert isinstance(stats["mean_delta_kl"], (float, int))
            assert isinstance(stats["std_delta_kl"], (float, int))

    def test_pilot_handles_nan_gracefully(self, tmp_path):
        """Test that the pilot analysis handles NaN values without crashing."""
        output_path = str(tmp_path / "test_pilot_nan.json")
        result = run_pilot_analysis(output_path=output_path, num_samples=5)
        
        # The function should complete even if some runs fail
        assert "config_review_flag" in result
        assert isinstance(result["config_review_flag"], bool)

    def test_monotonicity_check_logic(self, tmp_path):
        """Test the logic that checks for monotonicity or expected bounds."""
        output_path = str(tmp_path / "test_pilot_monotonic.json")
        result = run_pilot_analysis(output_path=output_path, num_samples=20)
        
        # Verify the summary contains stability scores
        for eps_str, stats in result["summary"].items():
            # Stability score should be non-negative
            assert stats["stability_score"] >= 0.0
            
            # If std is high, stability score should be low
            if stats["std_delta_kl"] > 0:
                expected_score = 1.0 / (stats["std_delta_kl"] + 1e-8)
                assert abs(stats["stability_score"] - expected_score) < 1e-6

    def test_run_results_structure(self, tmp_path):
        """Test the structure of individual run results."""
        output_path = str(tmp_path / "test_pilot_structure.json")
        result = run_pilot_analysis(output_path=output_path, num_samples=3)
        
        for run in result["run_results"]:
            assert "matrix_id" in run
            assert "seed" in run
            assert "epsilon_results" in run
            
            for eps_str, eps_data in run["epsilon_results"].items():
                assert "scaling_factor" in eps_data
                assert "delta_kl_proxy" in eps_data
                # Values should be numeric or NaN
                assert isinstance(eps_data["scaling_factor"], (float, int))
                assert isinstance(eps_data["delta_kl_proxy"], (float, int))
