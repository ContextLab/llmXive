"""
Contract test for analysis output schema (T019).

This test validates that the analysis results file (analysis/results.json)
conforms to the schema defined in contracts/output.schema.yaml.

Dependencies:
- T006: contracts/output.schema.yaml (analysis results schema definition)
"""

import json
import os
import re
import sys
from pathlib import Path

import yaml
import pytest

# Add the project root to the path if running from tests/
project_root = Path(__file__).parent.parent.parent
contracts_dir = project_root / "contracts"
analysis_dir = project_root / "analysis"

SCHEMA_PATH = contracts_dir / "output.schema.yaml"
RESULTS_PATH = analysis_dir / "results.json"


def load_schema():
    """Load the analysis output schema from YAML."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}. "
            "Ensure T006 (contracts/output.schema.yaml) is completed."
        )
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_results():
    """Load the analysis results JSON."""
    if not RESULTS_PATH.exists():
        pytest.fail(
            f"Results file not found: {RESULTS_PATH}. "
            "Ensure analysis script (code/analysis.py) has been run."
        )
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_type(value, expected_type, path=""):
    """Validate that a value matches the expected type."""
    if expected_type == "object":
        if not isinstance(value, dict):
            return False, f"Expected object at {path}, got {type(value).__name__}"
    elif expected_type == "array":
        if not isinstance(value, list):
            return False, f"Expected array at {path}, got {type(value).__name__}"
    elif expected_type == "string":
        if not isinstance(value, str):
            return False, f"Expected string at {path}, got {type(value).__name__}"
    elif expected_type == "number":
        if not isinstance(value, (int, float)):
            return False, f"Expected number at {path}, got {type(value).__name__}"
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            return False, f"Expected boolean at {path}, got {type(value).__name__}"
    elif expected_type == "integer":
        if not isinstance(value, int):
            return False, f"Expected integer at {path}, got {type(value).__name__}"
    return True, None


def validate_schema_recursive(data, schema_def, path=""):
    """Recursively validate data against schema definition."""
    if not isinstance(data, dict):
        # Handle array items if schema_def is for items
        if isinstance(schema_def, list) and len(schema_def) == 1:
            if not isinstance(data, list):
                return False, f"Expected array at {path}, got {type(data).__name__}"
            item_schema = schema_def[0]
            for i, item in enumerate(data):
                valid, err = validate_schema_recursive(item, item_schema, f"{path}[{i}]")
                if not valid:
                    return False, err
            return True, None
        return True, None

    if "type" in schema_def:
        valid, err = validate_type(data, schema_def["type"], path)
        if not valid:
            return False, err

    if schema_def.get("type") == "object" and "properties" in schema_def:
        for prop_name, prop_schema in schema_def["properties"].items():
            current_path = f"{path}.{prop_name}" if path else prop_name
            if prop_name in data:
                valid, err = validate_schema_recursive(data[prop_name], prop_schema, current_path)
                if not valid:
                    return False, err
            elif prop_schema.get("required", False):
                return False, f"Missing required property: {current_path}"

    if "required" in schema_def and isinstance(data, dict):
        for req_prop in schema_def["required"]:
            if req_prop not in data:
                return False, f"Missing required property: {path}.{req_prop}"

    return True, None


class TestAnalysisOutputSchema:
    """Contract tests for analysis output schema compliance."""

    @pytest.fixture(scope="class")
    def schema(self):
        """Load the analysis output schema."""
        return load_schema()

    @pytest.fixture(scope="class")
    def results(self):
        """Load the analysis results."""
        return load_results()

    def test_schema_file_exists(self, schema):
        """Test that the schema file is valid and loadable."""
        assert schema is not None, "Schema could not be loaded"
        assert isinstance(schema, dict), "Schema must be a dictionary"

    def test_results_file_exists(self, results):
        """Test that the results file exists and is valid JSON."""
        assert results is not None, "Results could not be loaded"
        assert isinstance(results, dict), "Results must be a dictionary"

    def test_top_level_structure(self, results):
        """Test that top-level required keys exist."""
        # Based on typical analysis results structure from T021, T027
        required_keys = ["model_summary", "effect_sizes", "mde_analysis", "convergence_status"]
        for key in required_keys:
            assert key in results, f"Missing required top-level key: {key}"

    def test_schema_compliance(self, schema, results):
        """Test that results conform to the defined schema."""
        valid, error = validate_schema_recursive(results, schema)
        assert valid, f"Results do not conform to schema: {error}"

    def test_model_summary_structure(self, results):
        """Test model summary has required fields."""
        summary = results.get("model_summary", {})
        assert "coef" in summary, "Missing 'coef' in model_summary"
        assert "pval" in summary, "Missing 'pval' in model_summary"
        assert "ci" in summary, "Missing 'ci' in model_summary"

    def test_effect_sizes_structure(self, results):
        """Test effect sizes have required fields."""
        effects = results.get("effect_sizes", [])
        assert isinstance(effects, list), "effect_sizes must be a list"
        if effects:
            effect = effects[0]
            assert "metric" in effect, "Missing 'metric' in effect_sizes entry"
            assert "value" in effect, "Missing 'value' in effect_sizes entry"
            assert "ci_lower" in effect, "Missing 'ci_lower' in effect_sizes entry"
            assert "ci_upper" in effect, "Missing 'ci_upper' in effect_sizes entry"

    def test_mde_analysis_structure(self, results):
        """Test MDE analysis has required fields."""
        mde = results.get("mde_analysis", {})
        assert "power" in mde, "Missing 'power' in mde_analysis"
        assert "mde_value" in mde, "Missing 'mde_value' in mde_analysis"
        assert "observed_effect" in mde, "Missing 'observed_effect' in mde_analysis"

    def test_convergence_status_structure(self, results):
        """Test convergence status has required fields."""
        conv = results.get("convergence_status", {})
        assert "converged" in conv, "Missing 'converged' in convergence_status"
        assert "message" in conv, "Missing 'message' in convergence_status"
        assert "rate" in conv, "Missing 'rate' in convergence_status"

    def test_fwer_control_status(self, results):
        """Test that FWER control status is logged."""
        assert "fwer_control_status" in results, "Missing 'fwer_control_status' in results"
        assert results["fwer_control_status"] in ["controlled", "not_applicable", "failed"], \
            "Invalid fwer_control_status value"

    def test_timestamp_format(self, results):
        """Test that timestamp is in ISO format."""
        if "timestamp" in results:
            timestamp = results["timestamp"]
            # Basic ISO format check
            assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", timestamp), \
                f"Invalid timestamp format: {timestamp}"

    def test_dataset_id_present(self, results):
        """Test that dataset_id is present in results."""
        assert "dataset_id" in results, "Missing 'dataset_id' in results"
        assert isinstance(results["dataset_id"], str), "dataset_id must be a string"
        assert len(results["dataset_id"]) > 0, "dataset_id cannot be empty"