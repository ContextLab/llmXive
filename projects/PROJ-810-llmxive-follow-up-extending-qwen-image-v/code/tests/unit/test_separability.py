import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest

from src.analysis.separability import calculate_sample_size_for_power, run_power_analysis

class TestCalculateSampleSize:
    def test_default_parameters(self):
        """Test sample size calculation with default effect_size=0.8, power=0.8."""
        n = calculate_sample_size_for_power(effect_size=0.8, power=0.8)
        # Expected: 2 * ((1.96 + 0.84) / 0.8)^2 ≈ 2 * (3.5)^2 ≈ 24.5 -> 25
        assert n >= 24
        assert n <= 30

    def test_larger_effect_size_requires_smaller_sample(self):
        """Larger effect size should require fewer samples."""
        n_small = calculate_sample_size_for_power(effect_size=0.8, power=0.8)
        n_large = calculate_sample_size_for_power(effect_size=1.2, power=0.8)
        assert n_large < n_small

    def test_higher_power_requires_larger_sample(self):
        """Higher power should require more samples."""
        n_low = calculate_sample_size_for_power(effect_size=0.8, power=0.8)
        n_high = calculate_sample_size_for_power(effect_size=0.8, power=0.95)
        assert n_high > n_low

class TestRunPowerAnalysis:
    def test_output_file_created(self):
        """Verify that the output JSON file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "results", "power.json")
            results = run_power_analysis(output_path, effect_size=0.8, power=0.8)
            
            assert os.path.exists(output_path)
            assert "N_required" in results
            assert "effect_size" in results
            assert "power" in results
            assert "N_audit" in results

    def test_json_content_valid(self):
        """Verify the JSON content matches the expected schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "results", "power.json")
            run_power_analysis(output_path, effect_size=0.8, power=0.8)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data["N_required"], int)
            assert data["N_required"] > 0
            assert data["effect_size"] == 0.8
            assert data["power"] == 0.8
            assert isinstance(data["N_audit"], int)
            assert data["N_audit"] > 0
            assert data["N_audit"] <= data["N_required"] or data["N_audit"] == 100