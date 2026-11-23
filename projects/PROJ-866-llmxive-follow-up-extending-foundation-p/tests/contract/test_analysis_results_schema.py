import pytest
import json
import yaml
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def load_schema(schema_path: str) -> dict:
    """Load a JSON schema from a YAML file."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_analysis_results(results: dict, schema: dict) -> bool:
    """Basic validation of analysis results against schema."""
    # Check required fields
    for field in schema.get("required", []):
        if field not in results:
            return False

    # Check numeric types
    for field in ["threshold_pct", "ci_lower", "ci_upper"]:
        if field in results:
            if not isinstance(results[field], (int, float)):
                return False

    return True


def test_analysis_results_schema():
    """Test that analysis results conform to the schema."""
    schema = load_schema("contracts/analysis_results.schema.yaml")

    # Create mock results
    results = {
        "threshold_pct": 35.5,
        "ci_lower": 30.2,
        "ci_upper": 40.8,
        "regression_coefficients": {
            "depth": 0.5,
            "complexity": 0.3,
            "intercept": 0.1
        }
    }

    assert validate_analysis_results(results, schema), "Results do not conform to schema"

    print("Analysis results schema test passed.")


if __name__ == "__main__":
    test_analysis_results_schema()
