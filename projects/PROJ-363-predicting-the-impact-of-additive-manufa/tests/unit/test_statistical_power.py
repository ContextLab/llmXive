import os
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path

# Import the module under test
from code.statistical_power import calculate_effect_size, calculate_power, analyze_power_from_permutation_report

def test_calculate_effect_size():
    # Cohen's d = mean_diff / std_dev
    mean_diff = 2.0
    std_dev = 1.0
    n = 10
    d = calculate_effect_size(mean_diff, std_dev, n)
    assert d == 2.0

    # Zero std dev should return 0 to avoid division by zero
    d_zero = calculate_effect_size(2.0, 0.0, 10)
    assert d_zero == 0.0

def test_calculate_power():
    # High effect size should yield high power
    power_high = calculate_power(1.0, 50)
    assert power_high > 0.8

    # Zero effect size should yield low power (near alpha)
    power_zero = calculate_power(0.0, 50)
    assert power_zero < 0.2

def test_analyze_power_from_permutation_report():
    # Create a mock report
    mock_report = {
        "results": [
            {"feature": "laser_power", "mean_importance": 0.5, "std_importance": 0.1, "p_value": 0.01, "n_samples": 100},
            {"feature": "scan_speed", "mean_importance": 0.1, "std_importance": 0.2, "p_value": 0.30, "n_samples": 100},
            {"feature": "hatch_spacing", "mean_importance": 0.8, "std_importance": 0.1, "p_value": 0.001, "n_samples": 100}
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "mock_report.json")
        output_path = os.path.join(tmpdir, "power_analysis.json")

        with open(input_path, 'w') as f:
            json.dump(mock_report, f)

        analyze_power_from_permutation_report(input_path, output_path)

        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            result = json.load(f)

        assert "features" in result
        assert len(result["features"]) == 3
        assert result["summary"]["high_power_features"] > 0
        assert result["summary"]["average_power"] > 0.0

        # Check specific feature
        laser_power_data = next(f for f in result["features"] if f["feature"] == "laser_power")
        assert laser_power_data["status"] == "High" # High effect size