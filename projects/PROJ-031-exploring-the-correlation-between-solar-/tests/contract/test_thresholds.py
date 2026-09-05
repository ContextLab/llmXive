"""
Contract test for Threshold Sweep Output Verification (T088b).

This test asserts that results/metrics.json contains the 'threshold_sensitivity' key
with entries specifically for 900, 1000, and 1100 km/s with corresponding True Positive Rates.

Dependency: T086 (End-to-End Regression Test) must have run successfully to produce
the metrics file.
"""
import os
import json
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METRICS_PATH = os.path.join(PROJECT_ROOT, "results", "metrics.json")

REQUIRED_SPEEDS = [900, 1000, 1100]
REQUIRED_KEYS = ["speed_kms", "true_positive_rate"]


def test_metrics_file_exists():
    """Assert that results/metrics.json exists."""
    assert os.path.exists(METRICS_PATH), f"Metrics file not found at {METRICS_PATH}. Run the pipeline first."


def test_metrics_json_valid():
    """Assert that results/metrics.json is valid JSON."""
    with open(METRICS_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in metrics file: {e}")
    return data


def test_threshold_sensitivity_key_exists():
    """Assert that 'threshold_sensitivity' key exists in metrics."""
    data = test_metrics_json_valid()
    assert "threshold_sensitivity" in data, (
        "Missing 'threshold_sensitivity' key in results/metrics.json. "
        "The analysis script must perform the sensitivity sweep."
    )


def test_threshold_sensitivity_structure():
    """
    Assert that 'threshold_sensitivity' contains entries for 900, 1000, and 1100 km/s.
    Each entry must have 'speed_kms' and 'true_positive_rate'.
    """
    data = test_metrics_json_valid()
    sensitivity_data = data["threshold_sensitivity"]

    # Ensure it's a list
    assert isinstance(sensitivity_data, list), (
        "'threshold_sensitivity' must be a list of dictionaries."
    )

    # Extract speeds found
    found_speeds = [entry["speed_kms"] for entry in sensitivity_data]

    # Verify required speeds are present
    missing_speeds = set(REQUIRED_SPEEDS) - set(found_speeds)
    assert not missing_speeds, (
        f"Missing threshold entries for speeds: {missing_speeds}. "
        f"Required speeds: {REQUIRED_SPEEDS}. Found: {found_speeds}."
    )

    # Verify structure of each entry
    for entry in sensitivity_data:
        assert isinstance(entry, dict), "Each entry in threshold_sensitivity must be a dictionary."
        assert "speed_kms" in entry, "Entry missing 'speed_kms'."
        assert "true_positive_rate" in entry, "Entry missing 'true_positive_rate'."
        
        # Validate types
        assert isinstance(entry["speed_kms"], (int, float)), "speed_kms must be numeric."
        assert isinstance(entry["true_positive_rate"], (int, float)), "true_positive_rate must be numeric."
        
        # Validate range (TPR should be between 0 and 1)
        tpr = entry["true_positive_rate"]
        assert 0.0 <= tpr <= 1.0, (
            f"True Positive Rate {tpr} for speed {entry['speed_kms']} is out of range [0, 1]."
        )

def test_specific_speed_entries():
    """
    Assert that specific entries for 900, 1000, and 1100 exist with valid TPR values.
    """
    data = test_metrics_json_valid()
    sensitivity_data = data["threshold_sensitivity"]
    
    speed_map = {entry["speed_kms"]: entry["true_positive_rate"] for entry in sensitivity_data}
    
    for speed in REQUIRED_SPEEDS:
        assert speed in speed_map, f"Speed {speed} not found in threshold_sensitivity."
        tpr = speed_map[speed]
        assert 0.0 <= tpr <= 1.0, f"Invalid TPR {tpr} for speed {speed}."