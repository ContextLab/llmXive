"""
Contract test for statistical analysis output format (T023).

This test verifies that the statistical analysis output files produced by
the evaluation pipeline (specifically T029: stats_analysis.py) adhere to
the strict schema defined in the project specification.

It ensures that:
1. The output file exists at the expected path.
2. The JSON structure contains the required keys: 'mean_metric', 'std_metric', 'n_seeds', 'seed_values'.
3. The data types are correct (floats for metrics, int for n_seeds, list for seed_values).
4. The values are within reasonable bounds (non-negative std, positive n_seeds).

This is a FAIL-FIRST test: it must run and fail against non-existent or malformed
output before the implementation (T029) is written.
"""
import os
import json
import pytest
from typing import Dict, Any, List

# Expected output path as per tasks.md and project structure
# T019c outputs to data/results/static_aggregated.json
# T026b outputs to data/results/baseline_aggregated.json
# T029 reads these and produces the final statistical comparison.
# The contract test checks the format of these aggregated files.
EXPECTED_STATIC_PATH = "data/results/static_aggregated.json"
EXPECTED_BASELINE_PATH = "data/results/baseline_aggregated.json"

# Required schema keys
REQUIRED_KEYS = {"mean_metric", "std_metric", "n_seeds", "seed_values"}

def load_json_file(path: str) -> Dict[str, Any]:
    """Helper to load JSON file, raising FileNotFoundError if missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Expected output file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_aggregated_schema(data: Dict[str, Any], source: str) -> None:
    """
    Validates the schema of an aggregated statistics file.
    
    Args:
        data: The loaded JSON dictionary.
        source: Name of the source file for error messages.
    
    Raises:
        AssertionError: If schema validation fails.
    """
    # Check required keys
    missing_keys = REQUIRED_KEYS - set(data.keys())
    assert not missing_keys, f"{source}: Missing required keys: {missing_keys}"
    
    # Type checks
    assert isinstance(data["mean_metric"], (int, float)), f"{source}: 'mean_metric' must be numeric"
    assert isinstance(data["std_metric"], (int, float)), f"{source}: 'std_metric' must be numeric"
    assert isinstance(data["n_seeds"], int), f"{source}: 'n_seeds' must be an integer"
    assert isinstance(data["seed_values"], list), f"{source}: 'seed_values' must be a list"
    
    # Value constraints
    assert data["n_seeds"] > 0, f"{source}: 'n_seeds' must be positive"
    assert data["std_metric"] >= 0, f"{source}: 'std_metric' cannot be negative"
    assert len(data["seed_values"]) == data["n_seeds"], f"{source}: Length of seed_values must match n_seeds"
    
    # Check that all seed values are numeric
    for i, val in enumerate(data["seed_values"]):
        assert isinstance(val, (int, float)), f"{source}: seed_values[{i}] must be numeric"

class TestStaticAggregatedOutput:
    """Contract tests for static_aggregated.json (T019c output)."""

    def test_file_exists(self):
        """Assert that the static aggregated file exists."""
        assert os.path.exists(EXPECTED_STATIC_PATH), \
            f"Contract failed: {EXPECTED_STATIC_PATH} does not exist. " \
            "Run T019c to generate this file."

    def test_schema_valid(self):
        """Assert that the static aggregated file matches the required schema."""
        data = load_json_file(EXPECTED_STATIC_PATH)
        validate_aggregated_schema(data, "static_aggregated.json")

    def test_mean_and_std_numeric(self):
        """Assert that mean and std are valid floats."""
        data = load_json_file(EXPECTED_STATIC_PATH)
        assert isinstance(data["mean_metric"], float) or isinstance(data["mean_metric"], int)
        assert isinstance(data["std_metric"], float) or isinstance(data["std_metric"], int)

    def test_seed_values_consistency(self):
        """Assert that seed_values length matches n_seeds."""
        data = load_json_file(EXPECTED_STATIC_PATH)
        assert len(data["seed_values"]) == data["n_seeds"]

class TestBaselineAggregatedOutput:
    """Contract tests for baseline_aggregated.json (T026b output)."""

    def test_file_exists(self):
        """Assert that the baseline aggregated file exists."""
        assert os.path.exists(EXPECTED_BASELINE_PATH), \
            f"Contract failed: {EXPECTED_BASELINE_PATH} does not exist. " \
            "Run T026b to generate this file."

    def test_schema_valid(self):
        """Assert that the baseline aggregated file matches the required schema."""
        data = load_json_file(EXPECTED_BASELINE_PATH)
        validate_aggregated_schema(data, "baseline_aggregated.json")

    def test_mean_and_std_numeric(self):
        """Assert that mean and std are valid floats."""
        data = load_json_file(EXPECTED_BASELINE_PATH)
        assert isinstance(data["mean_metric"], float) or isinstance(data["mean_metric"], int)
        assert isinstance(data["std_metric"], float) or isinstance(data["std_metric"], int)

    def test_seed_values_consistency(self):
        """Assert that seed_values length matches n_seeds."""
        data = load_json_file(EXPECTED_BASELINE_PATH)
        assert len(data["seed_values"]) == data["n_seeds"]

class TestStatisticalComparisonOutput:
    """Contract tests for the final statistical comparison output (T029)."""
    
    # The T029 task produces the final comparison. The output format isn't explicitly 
    # defined as a JSON file in the prompt for T029 itself, but it consumes the 
    # aggregated files. However, the contract test for T023 focuses on the 
    # *input* format to T029 (the aggregated files) to ensure T029 can run.
    # If T029 produces a specific report, it would be tested here too.
    # For now, we ensure the inputs (aggregated files) are valid.
    
    def test_inputs_valid_for_t29(self):
        """
        Assert that both static and baseline aggregated files are valid 
        so that T029 (stats_analysis.py) can proceed with the paired t-test.
        """
        # Load and validate static
        static_data = load_json_file(EXPECTED_STATIC_PATH)
        validate_aggregated_schema(static_data, "static_aggregated.json")
        
        # Load and validate baseline
        baseline_data = load_json_file(EXPECTED_BASELINE_PATH)
        validate_aggregated_schema(baseline_data, "baseline_aggregated.json")
        
        # Ensure both have the same metric type (e.g., both are perplexity or both are accuracy)
        # This is a heuristic check; the actual metric name might vary.
        # We assume the 'mean_metric' represents the same metric in both.
        assert type(static_data["mean_metric"]) == type(baseline_data["mean_metric"]), \
            "Static and Baseline metrics must be of the same numeric type."