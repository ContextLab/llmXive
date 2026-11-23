import os
import json
import pytest
import yaml
from pathlib import Path

# Adjust import based on project structure relative to test file
# Assuming tests/contract/ is at root relative to code/ or similar
# Using standard relative import for test execution from root
from pathlib import Path

RESULTS_SCHEMA_PATH = Path("contracts/results.schema.yaml")
ACCESS_CONTROL_RESULTS_PATH = Path("data/processed/access_control_results.json")

def load_schema(schema_path: Path) -> dict:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_results_against_schema(results: list, schema: dict) -> bool:
    """
    Validate that the results list matches the schema definition.
    
    The schema defines required keys and types.
    Expected keys based on T018/T019 tasks:
    [episode_id, method, score, latency_ms, peak_ram_mb]
    """
    required_keys = schema.get("required_keys", [])
    if not required_keys:
        # Fallback to common expectations if schema key missing
        required_keys = ["episode_id", "method", "score", "latency_ms", "peak_ram_mb"]
    
    if not isinstance(results, list):
        return False

    for idx, record in enumerate(results):
        if not isinstance(record, dict):
            raise AssertionError(f"Record at index {idx} is not a dictionary")
        
        for key in required_keys:
            if key not in record:
                raise AssertionError(f"Missing required key '{key}' in record at index {idx}")
            
            # Basic type validation if types are defined in schema
            type_map = schema.get("types", {})
            if key in type_map:
                expected_type = type_map[key]
                actual_type = type(record[key]).__name__
                # Simple string check for type matching
                if expected_type == "float" and not isinstance(record[key], (int, float)):
                    raise AssertionError(f"Key '{key}' in record {idx} should be float, got {actual_type}")
                if expected_type == "string" and not isinstance(record[key], str):
                    raise AssertionError(f"Key '{key}' in record {idx} should be string, got {actual_type}")
                if expected_type == "integer" and not isinstance(record[key], int):
                    raise AssertionError(f"Key '{key}' in record {idx} should be integer, got {actual_type}")

    return True

def test_access_control_results_matches_schema():
    """
    Contract test: Verify `data/processed/access_control_results.json` matches `results.schema.yaml`
    
    Assertion: `assert validate_results(data/processed/access_control_results.json, "results.schema.yaml")`
    """
    # 1. Check file existence
    assert ACCESS_CONTROL_RESULTS_PATH.exists(), \
        f"Results file not found: {ACCESS_CONTROL_RESULTS_PATH}. " \
        "Ensure T016/T018/T019 have been executed to generate this file."
    
    assert RESULTS_SCHEMA_PATH.exists(), \
        f"Schema file not found: {RESULTS_SCHEMA_PATH}. " \
        "Ensure T005a/T005 have been executed."

    # 2. Load data
    with open(ACCESS_CONTROL_RESULTS_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)

    # 3. Load schema
    schema = load_schema(RESULTS_SCHEMA_PATH)

    # 4. Validate
    assert validate_results_against_schema(results, schema), \
        "Results file structure does not match the results.schema.yaml definition."

    # 5. Additional sanity check: ensure at least one record exists
    assert len(results) > 0, "Results file is empty. No episodes were processed."

    # 6. Verify specific fields expected by the task description
    sample_record = results[0]
    assert "episode_id" in sample_record, "Missing 'episode_id' in results"
    assert "method" in sample_record, "Missing 'method' in results"
    assert "score" in sample_record, "Missing 'score' in results"
    assert "latency_ms" in sample_record, "Missing 'latency_ms' in results"
    assert "peak_ram_mb" in sample_record, "Missing 'peak_ram_mb' in results"

if __name__ == "__main__":
    test_access_control_results_matches_schema()
    print("Contract test passed: access_control_results.json matches schema.")