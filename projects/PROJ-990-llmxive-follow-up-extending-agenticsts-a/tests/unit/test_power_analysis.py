"""
Unit tests for the power analysis module (T044).
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Import the function to test
# We need to mock the file system dependencies or set up temporary files
import sys
sys.path.insert(0, 'code')

from power_analysis import calculate_power, load_sample_size, main

class TestCalculatePower:
    def test_power_increases_with_sample_size(self):
        # Power should increase as n increases for a fixed effect size
        p1 = calculate_power(50, 0.2, 0.05)["achieved_power"]
        p2 = calculate_power(200, 0.2, 0.05)["achieved_power"]
        p3 = calculate_power(500, 0.2, 0.05)["achieved_power"]

        assert p1 < p2 < p3
        assert p3 >= 0.8  # With n=500, power should be adequate for d=0.2

    def test_power_decreases_with_smaller_effect_size(self):
        # Power should decrease as effect size decreases
        p1 = calculate_power(300, 0.2, 0.05)["achieved_power"]
        p2 = calculate_power(300, 0.1, 0.05)["achieved_power"]

        assert p1 > p2

    def test_power_decreases_with_stricter_alpha(self):
        # Power should decrease as alpha decreases (harder to reject null)
        p1 = calculate_power(300, 0.2, 0.05)["achieved_power"]
        p2 = calculate_power(300, 0.2, 0.01)["achieved_power"]

        assert p1 > p2

    def test_output_structure(self):
        result = calculate_power(100, 0.2, 0.05)
        required_keys = [
            "sample_size", "effect_size", "alpha",
            "achieved_power", "target_power", "is_power_adequate", "warning"
        ]
        for key in required_keys:
            assert key in result

class TestLoadSampleSize:
    def test_load_from_train_set(self, tmp_path):
        # Create a temporary train_set.csv
        train_path = tmp_path / "train_set.csv"
        pd.DataFrame({"col1": range(100)}).to_csv(train_path)

        # Mock the global paths by temporarily patching
        import power_analysis
        original_train_path = power_analysis.TRAIN_SET_PATH
        power_analysis.TRAIN_SET_PATH = train_path
        power_analysis.TEST_SET_PATH = tmp_path / "nonexistent.csv"
        power_analysis.CONFIG_STATE_PATH = tmp_path / "nonexistent.json"

        try:
            n = load_sample_size()
            assert n == 100
        finally:
            power_analysis.TRAIN_SET_PATH = original_train_path

    def test_load_from_config_if_no_data(self, tmp_path):
        # Create a config_state.json with sample_size
        config_path = tmp_path / "config_state.json"
        with open(config_path, 'w') as f:
            json.dump({"sample_size": 250}, f)

        import power_analysis
        original_train = power_analysis.TRAIN_SET_PATH
        original_test = power_analysis.TEST_SET_PATH
        original_config = power_analysis.CONFIG_STATE_PATH

        power_analysis.TRAIN_SET_PATH = tmp_path / "no.csv"
        power_analysis.TEST_SET_PATH = tmp_path / "no.csv"
        power_analysis.CONFIG_STATE_PATH = config_path

        try:
            n = load_sample_size()
            assert n == 250
        finally:
            power_analysis.TRAIN_SET_PATH = original_train
            power_analysis.TEST_SET_PATH = original_test
            power_analysis.CONFIG_STATE_PATH = original_config

class TestMain:
    def test_main_creates_output(self, tmp_path):
        # Setup temp directory structure
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create a dummy train_set.csv
        (processed_dir / "train_set.csv").write_text("id,value\n1,10\n2,20\n3,30\n")

        import power_analysis
        original_output = power_analysis.OUTPUT_PATH
        original_train = power_analysis.TRAIN_SET_PATH

        power_analysis.OUTPUT_PATH = processed_dir / "power_analysis.json"
        power_analysis.TRAIN_SET_PATH = processed_dir / "train_set.csv"
        power_analysis.TEST_SET_PATH = tmp_path / "no.csv"
        power_analysis.CONFIG_STATE_PATH = tmp_path / "no.json"

        try:
            result = main()
            assert result is not None
            assert "achieved_power" in result
            assert result["sample_size"] == 3

            # Check file exists
            assert power_analysis.OUTPUT_PATH.exists()
            with open(power_analysis.OUTPUT_PATH) as f:
                data = json.load(f)
                assert "achieved_power" in data
        finally:
            power_analysis.OUTPUT_PATH = original_output
            power_analysis.TRAIN_SET_PATH = original_train