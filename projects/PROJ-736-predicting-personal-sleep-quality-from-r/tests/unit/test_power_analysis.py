"""Unit tests for power analysis module."""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling.power_analysis import (
    calculate_power_f_test,
    run_power_analysis,
    save_power_analysis
)


class TestCalculatePowerFTest:
    """Tests for calculate_power_f_test function."""

    def test_power_increases_with_sample_size(self):
        """Power should increase as sample size increases."""
        effect_size = 0.05
        alpha = 0.05

        power_small = calculate_power_f_test(effect_size, 50, alpha)
        power_large = calculate_power_f_test(effect_size, 200, alpha)

        assert power_large > power_small, "Power should increase with sample size"

    def test_power_increases_with_effect_size(self):
        """Power should increase as effect size increases."""
        sample_size = 100
        alpha = 0.05

        power_small = calculate_power_f_test(0.01, sample_size, alpha)
        power_large = calculate_power_f_test(0.10, sample_size, alpha)

        assert power_large > power_small, "Power should increase with effect size"

    def test_power_returns_valid_range(self):
        """Power should be between 0 and 1."""
        result = calculate_power_f_test(0.05, 100, 0.05)
        assert 0 <= result <= 1, f"Power should be between 0 and 1, got {result}"

    def test_power_decreases_with_alpha(self):
        """Power should decrease as alpha decreases (stricter threshold)."""
        effect_size = 0.05
        sample_size = 100

        power_alpha_05 = calculate_power_f_test(effect_size, sample_size, 0.05)
        power_alpha_01 = calculate_power_f_test(effect_size, sample_size, 0.01)

        assert power_alpha_05 >= power_alpha_01, "Power should decrease with stricter alpha"


class TestRunPowerAnalysis:
    """Tests for run_power_analysis function."""

    def test_returns_expected_keys(self):
        """Result should contain all required keys."""
        result = run_power_analysis()

        required_keys = ["effect_size", "sample_size", "power", "alpha", "status"]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_status_is_valid_or_invalid(self):
        """Status should be either 'valid' or 'invalid'."""
        result = run_power_analysis()
        assert result["status"] in ["valid", "invalid"], f"Invalid status: {result['status']}"

    def test_power_matches_threshold_logic(self):
        """Status should reflect whether power meets threshold."""
        target_power = 0.8
        result = run_power_analysis(target_power=target_power)

        if result["power"] >= target_power:
            assert result["status"] == "valid"
        else:
            assert result["status"] == "invalid"

    def test_effect_size_conversion(self):
        """Effect size should be preserved in result."""
        effect_size = 0.05
        result = run_power_analysis(effect_size_r2=effect_size)
        assert result["effect_size"] == effect_size


class TestSavePowerAnalysis:
    """Tests for save_power_analysis function."""

    def test_saves_valid_json(self):
        """Should save a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "power_analysis.json")
            results = {
                "effect_size": 0.05,
                "sample_size": 100,
                "power": 0.85,
                "alpha": 0.05,
                "status": "valid"
            }

            save_power_analysis(results, output_path)

            assert os.path.exists(output_path), "Output file was not created"

            with open(output_path, 'r') as f:
                loaded = json.load(f)

            assert loaded == results, "Saved results do not match input"

    def test_creates_directories(self):
        """Should create output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "power_analysis.json")
            results = {
                "effect_size": 0.05,
                "sample_size": 100,
                "power": 0.85,
                "alpha": 0.05,
                "status": "valid"
            }

            save_power_analysis(results, nested_path)

            assert os.path.exists(nested_path), "Output file was not created in nested directory"