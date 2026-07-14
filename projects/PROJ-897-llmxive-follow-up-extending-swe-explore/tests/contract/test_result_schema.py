"""
Contract test for result_schema.yaml.

Validates that all result artifacts produced by the analysis pipeline
strictly conform to the schema defined in contracts/result_schema.yaml.

This test ensures:
1. The schema file exists and is valid YAML.
2. The result artifacts (if they exist) match the schema structure.
3. Required fields are present and have correct types.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
import yaml

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.schemas import get_schema_path, load_schema
from utils.validation import validate_jsonl_against_schema, validate_parquet_against_schema


SCHEMA_FILE = "result_schema.yaml"
RESULTS_DIR = "data/results"
METRICS_FILE = "final_metrics.json"
PAIRED_METRICS_FILE = "paired_metrics.json"


def load_test_data(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file, handling potential missing files."""
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_test_data_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file, handling potential missing files."""
    if not filepath.exists():
        return []
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


class TestResultSchemaContract:
    """Tests verifying result artifacts against the result_schema.yaml contract."""

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the result schema from the contracts directory."""
        schema_path = get_schema_path(SCHEMA_FILE)
        assert schema_path.exists(), f"Schema file not found: {schema_path}"
        return load_schema(schema_path)

    def test_schema_exists_and_valid(self, schema: Dict[str, Any]) -> None:
        """Verify the schema file is valid YAML and has required structure."""
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "type" in schema, "Schema must define a 'type'"
        assert schema["type"] == "object", "Result schema type must be 'object'"
        assert "properties" in schema, "Schema must define 'properties'"

    def test_final_metrics_structure(self, schema: Dict[str, Any]) -> None:
        """
        Verify final_metrics.json (if it exists) conforms to the schema.
        
        This test checks the top-level structure and required fields
        defined in the schema for the final metrics output.
        """
        metrics_path = Path(RESULTS_DIR) / METRICS_FILE
        
        if not metrics_path.exists():
            # If the file doesn't exist yet, we skip the validation
            # but ensure the schema allows for the expected structure
            pytest.skip(f"Metrics file not found: {metrics_path}. "
                        "This is expected if analysis has not been run yet.")
        
        data = load_test_data(metrics_path)
        assert data, f"Metrics file is empty: {metrics_path}"
        
        # Validate against schema using the generic validator
        # We assume the schema defines the structure for the root object
        errors = []
        for key, expected_type in schema.get("properties", {}).items():
            if key not in data:
                # Check if it's required
                if key in schema.get("required", []):
                    errors.append(f"Missing required field: {key}")
            else:
                # Basic type check (schema might be more complex)
                value = data[key]
                type_name = expected_type.get("type") if isinstance(expected_type, dict) else expected_type
                
                if type_name == "number":
                    if not isinstance(value, (int, float)):
                        errors.append(f"Field '{key}' must be number, got {type(value).__name__}")
                elif type_name == "string":
                    if not isinstance(value, str):
                        errors.append(f"Field '{key}' must be string, got {type(value).__name__}")
                elif type_name == "array":
                    if not isinstance(value, list):
                        errors.append(f"Field '{key}' must be array, got {type(value).__name__}")
                elif type_name == "object":
                    if not isinstance(value, dict):
                        errors.append(f"Field '{key}' must be object, got {type(value).__name__}")

        assert not errors, f"Schema validation failed for {METRICS_FILE}: {errors}"

    def test_paired_metrics_structure(self, schema: Dict[str, Any]) -> None:
        """
        Verify paired_metrics.json (if it exists) conforms to the schema.
        
        This file contains the 1:1 paired results for Baseline vs Iterative.
        """
        paired_path = Path(RESULTS_DIR) / PAIRED_METRICS_FILE
        
        if not paired_path.exists():
            pytest.skip(f"Paired metrics file not found: {paired_path}. "
                        "This is expected if agent execution has not been run yet.")
        
        data = load_test_data(paired_path)
        assert data, f"Paired metrics file is empty: {paired_path}"
        
        # The paired metrics file might have a slightly different structure
        # (e.g., a list of records) than the aggregated final_metrics.
        # We check if it's a list of objects or a single object.
        if isinstance(data, list):
            # If it's a list, check the first item against the schema
            if len(data) > 0:
                first_item = data[0]
                assert isinstance(first_item, dict), "Paired metrics items must be objects"
                # Check for critical fields expected in paired data
                required_pair_fields = ["issue_id", "baseline_coverage", "iterative_coverage"]
                for field in required_pair_fields:
                    if field not in first_item:
                        # Log warning but don't fail if the schema allows it
                        # However, for this benchmark, these are critical
                        pytest.fail(f"Paired metric record missing critical field: {field}")
        elif isinstance(data, dict):
            # If it's a single object, validate against schema directly
            errors = []
            for key in schema.get("required", []):
                if key not in data:
                    errors.append(f"Missing required field: {key}")
            assert not errors, f"Schema validation failed for {PAIRED_METRICS_FILE}: {errors}"
        else:
            pytest.fail(f"Paired metrics file has invalid root type: {type(data)}")

    def test_schema_completeness(self, schema: Dict[str, Any]) -> None:
        """
        Verify the schema contains definitions for all expected result metrics.
        
        Based on the task requirements (T031), we expect specific fields
        related to coverage, ranking, and statistical tests.
        """
        properties = schema.get("properties", {})
        
        # Expected top-level sections based on FR-006 and T031
        expected_sections = [
            "coverage_metrics",
            "ranking_metrics", 
            "statistical_tests",
            "metadata"
        ]
        
        missing_sections = []
        for section in expected_sections:
            if section not in properties:
                missing_sections.append(section)
        
        if missing_sections:
            pytest.fail(f"Result schema missing expected sections: {missing_sections}. "
                        "The schema must define structures for coverage, ranking, "
                        "and statistical test results.")

    def test_statistical_test_schema(self, schema: Dict[str, Any]) -> None:
        """
        Verify the statistical_tests section of the schema includes
        fields for Wilcoxon signed-rank test results (p-value, statistic).
        """
        properties = schema.get("properties", {})
        if "statistical_tests" not in properties:
            pytest.skip("Statistical tests section not defined in schema yet.")
        
        stats_def = properties["statistical_tests"]
        if not isinstance(stats_def, dict):
            pytest.fail("statistical_tests must be an object definition.")
        
        # Check for nested properties if defined
        nested_props = stats_def.get("properties", {})
        
        # We expect at least coverage and ranking test results
        expected_test_types = ["coverage_wilcoxon", "ranking_wilcoxon"]
        missing_tests = [t for t in expected_test_types if t not in nested_props]
        
        if missing_tests:
            # This is a warning-level check; the schema might be evolving
            pytest.fail(f"Statistical test schema missing expected test types: {missing_tests}. "
                        "Must include Wilcoxon signed-rank results.")