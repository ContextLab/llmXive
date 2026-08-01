"""
Unit tests for the separability analysis module.
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Import the module under test
# We assume the project structure is: code/src/analysis/separability.py
# and we run tests from the code/ directory or root.
# Adjust import path based on actual execution context.
import sys
from pathlib import Path

# Add the src directory to the path if running from tests/
src_path = Path(__file__).resolve().parents[2] / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from analysis.separability import calculate_sample_size_for_power, run_power_analysis


class TestCalculateSampleSize:
    def test_standard_params(self):
        """Test with standard alpha=0.05, power=0.8, d=0.8"""
        n = calculate_sample_size_for_power(effect_size=0.8, power=0.8, alpha=0.05)
        # Expected approx: 2 * ((1.96 + 0.84) / 0.8)^2 = 2 * (3.5)^2 = 2 * 12.25 = 24.5 -> 25 per group
        # Let's verify the math:
        # Z_alpha/2 = 1.96, Z_beta = 0.84
        # N = 2 * (2.8 / 0.8)^2 = 2 * (3.5)^2 = 24.5 -> 25
        assert n >= 24  # Allow slight variation due to Z-score precision

    def test_high_power_requires_more(self):
        """Higher power should require larger N"""
        n_80 = calculate_sample_size_for_power(power=0.80)
        n_90 = calculate_sample_size_for_power(power=0.90)
        assert n_90 > n_80

    def test_larger_effect_requires_less(self):
        """Larger effect size should require smaller N"""
        n_small_d = calculate_sample_size_for_power(effect_size=0.5)
        n_large_d = calculate_sample_size_for_power(effect_size=1.0)
        assert n_small_d > n_large_d

    def test_return_type_is_int(self):
        """Ensure the return value is an integer (rounded up)"""
        n = calculate_sample_size_for_power()
        assert isinstance(n, int)
        assert n > 0


class TestRunPowerAnalysis:
    def test_creates_json_file(self):
        """Test that the function creates the output JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power.json"
            results = run_power_analysis(output_path=output_path)

            assert output_path.exists()
            assert results is not None
            assert "N_required" in results
            assert "N_audit" in results
            assert "effect_size" in results

    def test_json_content_structure(self):
        """Test that the JSON contains all required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power.json"
            run_power_analysis(output_path=output_path)

            with open(output_path, "r") as f:
                data = json.load(f)

            required_keys = ["N_required", "N_per_group", "effect_size", "power", "alpha", "N_audit"]
            for key in required_keys:
                assert key in data, f"Missing required key: {key}"

    def test_n_audit_is_reasonable(self):
        """Test that N_audit is capped or reasonable"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power.json"
            results = run_power_analysis(output_path=output_path)

            # N_audit should be positive and not exceed a reasonable manual audit limit (e.g., 200)
            assert 0 < results["N_audit"] <= 200
            # N_audit should not exceed N_per_group
            assert results["N_audit"] <= results["N_per_group"]
