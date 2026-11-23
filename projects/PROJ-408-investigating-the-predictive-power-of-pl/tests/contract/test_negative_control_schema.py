"""
Contract test for T012 Negative Control output schema.
Verifies that the JSON output matches the expected structure.
"""
import json
import pytest
from pathlib import Path

from config import get_config


def test_negative_control_output_schema():
    """
    Asserts that the negative control results file exists and matches the schema.
    """
    config = get_config()
    output_path = config.PROCESSED_DATA_DIR / "negative_control_results.json"
    
    # The test file T012 should have been run to produce this.
    # If it doesn't exist, we assume the test hasn't been run yet, 
    # but for the contract test to be valid, it should exist.
    if not output_path.exists():
        pytest.skip("Negative control results file not found. Run T012 first.")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # Schema assertions
    required_keys = [
        "test_name", "seed", "n_permutations", "observed_r", 
        "observed_p", "threshold", "passed", 
        "null_distribution_mean", "null_distribution_std"
    ]
    
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    # Type assertions
    assert isinstance(data["test_name"], str)
    assert isinstance(data["seed"], int)
    assert isinstance(data["n_permutations"], int)
    assert isinstance(data["observed_r"], float)
    assert isinstance(data["observed_p"], float)
    assert isinstance(data["threshold"], float)
    assert isinstance(data["passed"], bool)
    assert isinstance(data["null_distribution_mean"], float)
    assert isinstance(data["null_distribution_std"], float)
    
    # Value assertions
    assert data["threshold"] == 0.05
    assert data["passed"] is True, f"Negative control failed: |r|={data['observed_r']} >= {data['threshold']}"
    
    # Ensure r is small
    assert abs(data["observed_r"]) < 0.05, f"Correlation too high: {data['observed_r']}"