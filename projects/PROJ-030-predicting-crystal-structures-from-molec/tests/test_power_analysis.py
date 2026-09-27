"""
Tests for Power Analysis module (T006b).
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.power import calculate_sample_size, run_power_analysis, main


class TestPowerAnalysis:
    """Test cases for power analysis calculations."""

    def test_calculate_sample_size_minimum(self):
        """Test that calculated sample size is positive and reasonable."""
        result = calculate_sample_size(0.15, 0.05, 0.80)
        assert result > 0
        assert result < 10000  # Reasonable upper bound

    def test_calculate_sample_size_effect_size_sensitivity(self):
        """Test that smaller effect size requires larger sample."""
        n_large_effect = calculate_sample_size(0.30, 0.05, 0.80)
        n_small_effect = calculate_sample_size(0.15, 0.05, 0.80)
        assert n_small_effect > n_large_effect

    def test_calculate_sample_size_power_sensitivity(self):
        """Test that higher power requires larger sample."""
        n_low_power = calculate_sample_size(0.15, 0.05, 0.70)
        n_high_power = calculate_sample_size(0.15, 0.05, 0.90)
        assert n_high_power > n_low_power

    def test_run_power_analysis_structure(self):
        """Test that run_power_analysis returns expected structure."""
        results = run_power_analysis()
        assert "parameters" in results
        assert "calculated_metrics" in results
        assert "assumptions" in results
        assert "recommendation" in results
        assert "planning_artifact" in results

    def test_run_power_analysis_target_scaffolds(self):
        """Test that target scaffolds is at least 500."""
        results = run_power_analysis()
        target = results["calculated_metrics"]["final_target_sample_size"]
        assert target >= 500

    def test_run_power_analysis_effect_size_param(self):
        """Test that effect size parameter is correctly set."""
        results = run_power_analysis()
        assert results["parameters"]["effect_size_w"] == 0.15

    def test_run_power_analysis_alpha_param(self):
        """Test that alpha parameter is correctly set."""
        results = run_power_analysis()
        assert results["parameters"]["significance_alpha"] == 0.05

    def test_run_power_analysis_power_param(self):
        """Test that power parameter is correctly set."""
        results = run_power_analysis()
        assert results["parameters"]["statistical_power"] == 0.80

    def test_main_creates_output_file(self):
        """Test that main() creates the output JSON file."""
        # Run main
        main()

        # Check file exists
        output_path = Path(__file__).parent.parent / "code" / ".." / "data" / "power_analysis_metrics.json"
        # Normalize path
        output_path = output_path.resolve()
        assert output_path.exists()

        # Check file is valid JSON with expected keys
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert "parameters" in data
            assert "calculated_metrics" in data
            assert data["planning_artifact"] == "T006b"

    def test_main_output_content(self):
        """Test that main() output contains correct values."""
        main()
        output_path = Path(__file__).parent.parent / "code" / ".." / "data" / "power_analysis_metrics.json"
        output_path = output_path.resolve()

        with open(output_path, 'r') as f:
            data = json.load(f)

        # Verify key metrics
        assert data["parameters"]["effect_size_w"] == 0.15
        assert data["parameters"]["significance_alpha"] == 0.05
        assert data["calculated_metrics"]["domain_target_scaffolds"] == 500
        assert data["calculated_metrics"]["final_target_sample_size"] >= 500

    def test_recommendation_format(self):
        """Test that recommendation string contains expected target."""
        results = run_power_analysis()
        recommendation = results["recommendation"]
        assert "scaffolds" in recommendation
        assert "Target" in recommendation
        assert str(results["calculated_metrics"]["final_target_sample_size"]) in recommendation