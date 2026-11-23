"""
Unit test for ``code/models/verify_baseline_metrics.py``.

The test simply runs the ``main`` function and checks that the expected
JSON file is created and contains the required keys with numeric values.
It does **not** assert any particular performance thresholds – those are
part of the research analysis, not the CI contract.
"""

import json
from pathlib import Path

import pytest

# Import the script's entry point
from models.verify_baseline_metrics import main as verify_main


@pytest.fixture(scope="module")
def result_path():
    """Path to the verification JSON file."""
    return Path("data/results/baseline_verification.json")


def test_verification_file_creation(result_path):
    # Ensure a clean state before running the script
    if result_path.is_file():
        result_path.unlink()

    # Run the verification script
    verify_main()

    # The file must now exist
    assert result_path.is_file(), "Verification JSON file was not created."

    # Load and inspect the JSON content
    with result_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Expected keys
    expected_keys = {"random_forest_r2", "gradient_boosting_r2", "timestamp"}
    assert expected_keys.issubset(data.keys()), "Missing keys in verification report."

    # R² scores should be floats (could be negative if model is poor)
    assert isinstance(data["random_forest_r2"], float), "RF R² is not a float."
    assert isinstance(data["gradient_boosting_r2"], float), "GB R² is not a float."

    # Timestamp should be a string in ISO format (basic sanity check)
    assert isinstance(data["timestamp"], str) and len(data["timestamp"]) > 0, "Timestamp missing or malformed."