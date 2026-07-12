"""
Unit tests for src/analysis/separability.py
"""
import json
import math
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from scipy.stats import norm

# Add src to path if running directly, though typically pytest handles this via conftest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from analysis.separability import calculate_sample_size_power, run_power_analysis


class TestCalculateSampleSizePower:
    def test_standard_large_effect(self):
        """Test calculation with standard large effect size (0.8)"""
        n = calculate_sample_size_power(effect_size=0.8, alpha=0.05, power=0.80)
        # Expected approx: 2 * ((1.96 + 0.84) / 0.8)^2 ≈ 2 * (3.5)^2 ≈ 2 * 12.25 ≈ 24.5 -> 25
        assert n >= 24
        assert n <= 30

    def test_small_effect_requires_larger_n(self):
        """Smaller effect size should require larger N"""
        n_small = calculate_sample_size_power(effect_size=0.2)
        n_large = calculate_sample_size_power(effect_size=0.8)
        assert n_small > n_large

    def test_high_power_requires_larger_n(self):
        """Higher power should require larger N"""
        n_80 = calculate_sample_size_power(effect_size=0.8, power=0.80)
        n_90 = calculate_sample_size_power(effect_size=0.8, power=0.90)
        assert n_90 > n_80


class TestRunPowerAnalysis:
    def test_output_structure(self, tmp_path):
        """Verify the output JSON structure"""
        # Temporarily redirect output dir
        original_dir = Path("data/results")
        temp_dir = tmp_path / "data" / "results"
        temp_dir.mkdir(parents=True)

        with patch("analysis.separability.OUTPUT_DIR", temp_dir):
            result = run_power_analysis(effect_size=0.8)

        # Check keys
        assert "N_required" in result
        assert "effect_size" in result
        assert "power" in result
        assert "N_audit" in result
        assert result["effect_size"] == 0.8
        assert result["power"] == 0.80
        assert result["N_required"] > 0
        assert result["N_audit"] > 0
        assert result["N_audit"] <= result["N_required"]

    def test_file_creation(self, tmp_path):
        """Verify the JSON file is actually written to disk"""
        temp_dir = tmp_path / "data" / "results"
        temp_dir.mkdir(parents=True)

        with patch("analysis.separability.OUTPUT_DIR", temp_dir):
            run_power_analysis(effect_size=0.8)

        output_file = temp_dir / "power_analysis.json"
        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert "N_required" in data
        assert isinstance(data["N_required"], int)

    def test_audit_calculation(self, tmp_path):
        """Verify N_audit logic (min 30, or 5% of N)"""
        temp_dir = tmp_path / "data" / "results"
        temp_dir.mkdir(parents=True)

        # Force a very small N_required to test min_audit logic
        # We mock the calculation function to return a small number
        with patch("analysis.separability.calculate_sample_size_power", return_value=50):
            with patch("analysis.separability.OUTPUT_DIR", temp_dir):
                result = run_power_analysis(effect_size=0.8, audit_ratio=0.05, min_audit=30)

        # 5% of 50 is 2.5 -> 2. Min audit is 30. So N_audit should be 30.
        assert result["N_audit"] == 30

        # Force a large N_required
        with patch("analysis.separability.calculate_sample_size_power", return_value=1000):
            with patch("analysis.separability.OUTPUT_DIR", temp_dir):
                result = run_power_analysis(effect_size=0.8, audit_ratio=0.05, min_audit=30)

        # 5% of 1000 is 50. Min audit is 30. So N_audit should be 50.
        assert result["N_audit"] == 50
