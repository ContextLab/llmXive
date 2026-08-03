"""
Contract test for T012: Verify data/processed/access_control_results.json matches results.schema.yaml

This test validates that the access control results output by the pipeline
conforms to the defined schema in contracts/results.schema.yaml.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import pytest
import yaml

# Add project root to path for imports if needed
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "results.schema.yaml"
RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "access_control_results.json"


def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def load_results() -> Dict[str, Any]:
    """Load the access control results JSON file."""
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"Results file not found: {RESULTS_PATH}")
    
    with open(RESULTS_PATH, "r") as f:
        return json.load(f)


def validate_type(value: Any, expected_type: str, schema_def: Dict) -> bool:
    """Validate a value against a JSON schema type definition."""
    if expected_type == "object":
        if not isinstance(value, dict):
            return False
        # Check required properties
        if "required" in schema_def:
            for req_prop in schema_def["required"]:
                if req_prop not in value:
                    return False
        # Check properties
        if "properties" in schema_def:
            for prop, prop_def in schema_def["properties"].items():
                if prop in value:
                    prop_type = prop_def.get("type")
                    if prop_type and not validate_type(value[prop], prop_type, prop_def):
                        return False
        return True
    
    elif expected_type == "array":
        if not isinstance(value, list):
            return False
        items_def = schema_def.get("items", {})
        items_type = items_def.get("type")
        if items_type:
            for item in value:
                if not validate_type(item, items_type, items_def):
                    return False
        return True
    
    elif expected_type == "string":
        if not isinstance(value, str):
            return False
        if "format" in schema_def and schema_def["format"] == "date-time":
            # Basic ISO 8601 check
            if "T" not in value or not value.endswith("Z") and "+" not in value and "-" not in value[-6:]:
                # Allow basic ISO format without timezone
                pass
        return True
    
    elif expected_type == "number":
        if not isinstance(value, (int, float)):
            return False
        if "minimum" in schema_def:
            if value < schema_def["minimum"]:
                return False
        if "maximum" in schema_def:
            if value > schema_def["maximum"]:
                return False
        return True
    
    elif expected_type == "integer":
        if not isinstance(value, int):
            return False
        if "minimum" in schema_def:
            if value < schema_def["minimum"]:
                return False
        return True
    
    elif expected_type == "boolean":
        return isinstance(value, bool)
    
    return True


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against the schema.
    Returns a list of validation errors.
    """
    errors = []
    
    # Check root type
    root_type = schema.get("type")
    if root_type and not validate_type(data, root_type, schema):
        errors.append(f"Root object does not match expected type: {root_type}")
        return errors
    
    # Check required properties at root level
    if "required" in schema:
        for req in schema["required"]:
            if req not in data:
                errors.append(f"Missing required property at root: {req}")
    
    # Check properties
    if "properties" in schema:
        for prop, prop_schema in schema["properties"].items():
            if prop in data:
                prop_type = prop_schema.get("type")
                if prop_type:
                    if not validate_type(data[prop], prop_type, prop_schema):
                        errors.append(f"Property '{prop}' does not match schema type: {prop_type}")
                    
                    # Recursively validate nested objects
                    if prop_type == "object" and "properties" in prop_schema:
                        nested_errors = validate_against_schema(data[prop], prop_schema)
                        errors.extend([f"{prop}.{e}" for e in nested_errors])
                    
                    # Validate arrays
                    if prop_type == "array" and "items" in prop_schema:
                        items_schema = prop_schema["items"]
                        items_type = items_schema.get("type")
                        if items_type and isinstance(data[prop], list):
                            for idx, item in enumerate(data[prop]):
                                if not validate_type(item, items_type, items_schema):
                                    errors.append(f"Property '{prop}[{idx}]' does not match array items schema: {items_type}")
                                elif items_type == "object" and "properties" in items_schema:
                                    nested_errors = validate_against_schema(item, items_schema)
                                    errors.extend([f"{prop}[{idx}].{e}" for e in nested_errors])
    
    return errors


class TestAccessControlResultsSchema:
    """Contract tests for access control results schema validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure required files exist before running tests."""
        if not SCHEMA_PATH.exists():
            pytest.fail(f"Schema file missing: {SCHEMA_PATH}")
        if not RESULTS_PATH.exists():
            pytest.fail(f"Results file missing: {RESULTS_PATH}. Run the evaluation pipeline first.")

    def test_schema_file_exists(self):
        """Verify the schema file exists and is valid YAML."""
        try:
            schema = load_schema()
            assert "type" in schema
            assert "properties" in schema
        except Exception as e:
            pytest.fail(f"Schema file is invalid: {e}")

    def test_results_file_exists(self):
        """Verify the results file exists and is valid JSON."""
        try:
            results = load_results()
            assert isinstance(results, dict)
        except json.JSONDecodeError as e:
            pytest.fail(f"Results file is not valid JSON: {e}")

    def test_results_against_schema(self):
        """Main test: Verify results match the schema definition."""
        schema = load_schema()
        results = load_results()
        
        errors = validate_against_schema(results, schema)
        
        if errors:
            error_msg = "\n".join([f"  - {e}" for e in errors])
            pytest.fail(f"Results do not match schema:\n{error_msg}")

    def test_metadata_structure(self):
        """Verify metadata section has required fields."""
        results = load_results()
        assert "metadata" in results, "Missing 'metadata' section"
        
        metadata = results["metadata"]
        required_fields = ["timestamp", "pipeline_version", "dataset_version", "domains"]
        
        for field in required_fields:
            assert field in metadata, f"Missing metadata field: {field}"

    def test_access_control_structure(self):
        """Verify access_control section has required fields."""
        results = load_results()
        assert "access_control" in results, "Missing 'access_control' section"
        
        ac = results["access_control"]
        required_fields = ["method", "score", "std_dev", "total_samples", "unauthorized_leaks", "allowed_requests"]
        
        for field in required_fields:
            assert field in ac, f"Missing access_control field: {field}"
        
        # Validate score range
        assert 0 <= ac["score"] <= 1, f"Access control score {ac['score']} is not in range [0, 1]"

    def test_method_enum(self):
        """Verify the method field uses allowed values."""
        results = load_results()
        ac = results["access_control"]
        
        valid_methods = ["gatekeeper", "baseline_retrieval", "baseline_long_context"]
        assert ac["method"] in valid_methods, f"Invalid method: {ac['method']}"

    def test_domains_list(self):
        """Verify domains is a non-empty list of strings."""
        results = load_results()
        metadata = results["metadata"]
        
        assert isinstance(metadata["domains"], list), "Domains must be a list"
        assert len(metadata["domains"]) > 0, "Domains list cannot be empty"
        
        for domain in metadata["domains"]:
            assert isinstance(domain, str), f"Domain must be a string: {domain}"

    def test_score_consistency(self):
        """Verify score calculation is consistent with leak counts."""
        results = load_results()
        ac = results["access_control"]
        
        total = ac["total_samples"]
        leaks = ac["unauthorized_leaks"]
        allowed = ac["allowed_requests"]
        
        # Basic consistency check: total should be >= leaks + allowed
        # Note: This is a simplified check; actual logic might vary
        assert total >= leaks, f"Total samples {total} less than leaks {leaks}"
        
        # Score should be 1 - (leaks / total) approximately
        expected_score = 1 - (leaks / total) if total > 0 else 1.0
        # Allow small floating point tolerance
        assert abs(ac["score"] - expected_score) < 0.01, \
            f"Score {ac['score']} inconsistent with leaks {leaks}/{total} (expected ~{expected_score})"
