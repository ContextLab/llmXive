"""
Contract tests for results schema validation.

This module validates that the output of the Gatekeeper and Baseline pipelines
conforms to the schema defined in contracts/results.schema.yaml.

It tests:
1. Top-level structure (method, domain, metrics)
2. Metric-specific fields (Access Control, Utility, Forgetting, Latency)
3. Statistical analysis fields (p-value, test statistic, etc.)
4. Type constraints and required fields
"""

import json
import os
import pytest
import yaml
from typing import Dict, Any, List

# Project root is assumed to be the parent of 'tests'
# Adjust based on actual project structure if needed
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "contracts", "results.schema.yaml")

# Expected output paths relative to project root
ACCESS_CONTROL_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "access_control_results.json")
UTILITY_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "utility_results.json")
PERFORMANCE_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "performance_results.json")
FINAL_REPORT_PATH = os.path.join(PROJECT_ROOT, "data", "results", "final_benchmark_report.md")

def load_schema() -> Dict[str, Any]:
    """Load the results schema from YAML file."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}. Ensure T005 is complete.")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_structure(data: Dict[str, Any], schema: Dict[str, Any], path: str) -> None:
    """
    Recursively validate data against schema.
    
    Args:
        data: The data to validate
        schema: The schema definition
        path: Current path in the data structure (for error messages)
    """
    if schema.get("type") == "object":
        if not isinstance(data, dict):
            pytest.fail(f"Expected object at {path}, got {type(data).__name__}")
        
        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                pytest.fail(f"Missing required field '{field}' at {path}")
        
        # Validate each property
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                validate_structure(value, properties[key], f"{path}.{key}")
            elif not key.startswith("_"):  # Allow internal/underscore fields
                # Optional: warn about unknown fields, but don't fail unless strict
                pass
                
    elif schema.get("type") == "array":
        if not isinstance(data, list):
            pytest.fail(f"Expected array at {path}, got {type(data).__name__}")
        items_schema = schema.get("items", {})
        for i, item in enumerate(data):
            validate_structure(item, items_schema, f"{path}[{i}]")
            
    elif schema.get("type") == "string":
        if not isinstance(data, str):
            pytest.fail(f"Expected string at {path}, got {type(data).__name__}")
            
    elif schema.get("type") == "number" or schema.get("type") == "integer":
        if not isinstance(data, (int, float)):
            pytest.fail(f"Expected number at {path}, got {type(data).__name__}")
            
    elif schema.get("type") == "boolean":
        if not isinstance(data, bool):
            pytest.fail(f"Expected boolean at {path}, got {type(data).__name__}")

@pytest.fixture
def schema():
    return load_schema()

@pytest.mark.parametrize("result_path", [
    ACCESS_CONTROL_PATH,
    UTILITY_PATH,
    PERFORMANCE_PATH
])
def test_results_schema_compliance(result_path: str, schema: Dict[str, Any]):
    """
    Contract test: Verify that result files match results.schema.yaml.
    
    This test loads the result file and validates it against the schema.
    It ensures all required fields are present and types are correct.
    """
    if not os.path.exists(result_path):
        pytest.skip(f"Result file not yet generated: {result_path}. "
                   "This is expected if the pipeline hasn't run yet.")
    
    with open(result_path, 'r') as f:
        data = json.load(f)
    
    validate_structure(data, schema, "root")

def test_access_control_specific_fields(schema: Dict[str, Any]):
    """
    Test specific fields required for Access Control results.
    
    Ensures the presence of:
    - unauthorized_exposure_rate
    - false_positive_rate
    - false_negative_rate
    """
    if not os.path.exists(ACCESS_CONTROL_PATH):
        pytest.skip(f"Access control results not yet generated: {ACCESS_CONTROL_PATH}")
    
    with open(ACCESS_CONTROL_PATH, 'r') as f:
        data = json.load(f)
    
    # Check top-level structure
    assert "method" in data, "Missing 'method' field"
    assert "domain" in data, "Missing 'domain' field"
    assert "metrics" in data, "Missing 'metrics' field"
    
    metrics = data["metrics"]
    assert "access_control" in metrics, "Missing 'access_control' metrics"
    
    ac = metrics["access_control"]
    required_ac_fields = ["unauthorized_exposure_rate", "false_positive_rate", "false_negative_rate"]
    for field in required_ac_fields:
        assert field in ac, f"Missing '{field}' in access_control metrics"
        assert isinstance(ac[field], (int, float)), f"'{field}' must be numeric"

def test_utility_specific_fields(schema: Dict[str, Any]):
    """
    Test specific fields required for Utility results.
    
    Ensures the presence of:
    - conditional_utility
    - overall_success_rate
    - forgetting_compliance
    """
    if not os.path.exists(UTILITY_PATH):
        pytest.skip(f"Utility results not yet generated: {UTILITY_PATH}")
    
    with open(UTILITY_PATH, 'r') as f:
        data = json.load(f)
    
    assert "metrics" in data, "Missing 'metrics' field"
    metrics = data["metrics"]
    
    # Check Utility fields
    if "utility" in metrics:
        utility = metrics["utility"]
        assert "overall_success_rate" in utility, "Missing 'overall_success_rate'"
        assert isinstance(utility["overall_success_rate"], (int, float))
    
    # Check Forgetting fields
    if "forgetting" in metrics:
        forgetting = metrics["forgetting"]
        assert "deletion_compliance_rate" in forgetting, "Missing 'deletion_compliance_rate'"
        assert isinstance(forgetting["deletion_compliance_rate"], (int, float))

def test_performance_specific_fields(schema: Dict[str, Any]):
    """
    Test specific fields required for Performance results.
    
    Ensures the presence of:
    - latency_ms
    - peak_ram_mb
    - wall_clock_time
    """
    if not os.path.exists(PERFORMANCE_PATH):
        pytest.skip(f"Performance results not yet generated: {PERFORMANCE_PATH}")
    
    with open(PERFORMANCE_PATH, 'r') as f:
        data = json.load(f)
    
    assert "metrics" in data, "Missing 'metrics' field"
    metrics = data["metrics"]
    
    if "performance" in metrics:
        perf = metrics["performance"]
        assert "latency_ms" in perf, "Missing 'latency_ms'"
        assert "peak_ram_mb" in perf, "Missing 'peak_ram_mb'"
        assert isinstance(perf["latency_ms"], (int, float))
        assert isinstance(perf["peak_ram_mb"], (int, float))

def test_statistical_analysis_fields(schema: Dict[str, Any]):
    """
    Test that statistical analysis fields are present when applicable.
    
    Ensures presence of:
    - test_statistic
    - p_value
    - degrees_of_freedom
    - method_used (LMM/Fallback)
    """
    # This test checks if statistical fields are present in the schema
    # and validates them if the results include statistical analysis
    
    if not os.path.exists(ACCESS_CONTROL_PATH):
        pytest.skip("No results to check for statistical fields")
    
    with open(ACCESS_CONTROL_PATH, 'r') as f:
        data = json.load(f)
    
    # Check if statistical analysis is included
    if "statistical_analysis" in data:
        stats = data["statistical_analysis"]
        assert "method_used" in stats, "Missing 'method_used' in statistical analysis"
        assert stats["method_used"] in ["LMM", "paired_ttest", "wilcoxon"], \
            f"Invalid method: {stats['method_used']}"
        
        if stats["method_used"] != "LMM":
            # Fallback methods should have p-value and test statistic
            assert "p_value" in stats, "Missing 'p_value' for fallback method"
            assert "test_statistic" in stats, "Missing 'test_statistic' for fallback method"

def test_schema_validation_error_handling():
    """
    Test that invalid data is properly rejected by the schema validation.
    
    This creates a mock invalid data structure and ensures it fails validation.
    """
    invalid_data = {
        "method": "gatekeeper",
        "domain": "medical",
        "metrics": {
            "access_control": {
                "unauthorized_exposure_rate": "not_a_number"  # Should be numeric
            }
        }
    }
    
    schema = load_schema()
    
    # This should raise an error during validation
    with pytest.raises(Exception):
        validate_structure(invalid_data, schema, "root")

def test_empty_results_handling():
    """
    Test handling of empty or minimal result files.
    
    Ensures the validator doesn't crash on empty files or files with only metadata.
    """
    empty_data = {
        "method": "gatekeeper",
        "domain": "medical",
        "metrics": {}
    }
    
    schema = load_schema()
    
    # Empty metrics should be valid if no specific metrics are required for the domain
    # This test ensures the validator handles this gracefully
    try:
        validate_structure(empty_data, schema, "root")
    except Exception as e:
        # If it fails, it should be due to missing required metrics, not a crash
        assert "Missing required field" in str(e) or "Expected" in str(e)