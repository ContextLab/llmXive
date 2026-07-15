"""
Contract tests to verify the existence and basic validity of schema files.
These tests ensure that the required YAML schemas are present and parseable.
"""
import os
import pytest
from pathlib import Path
import yaml
import sys

# Ensure code directory is in path
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.schemas import get_schema_path, load_schema, SCHEMA_FILES

class TestSchemaExistence:
    """Tests to verify that all required schema files exist."""

    @pytest.mark.parametrize("schema_type", SCHEMA_FILES.keys())
    def test_schema_file_exists(self, schema_type):
        """Verify that the schema file for the given type exists on disk."""
        path = get_schema_path(schema_type)
        assert path.exists(), f"Schema file missing: {path}"
        assert path.is_file(), f"Schema path is not a file: {path}"

class TestSchemaValidity:
    """Tests to verify that schema files are valid YAML and have required structure."""

    @pytest.mark.parametrize("schema_type", SCHEMA_FILES.keys())
    def test_schema_is_valid_yaml(self, schema_type):
        """Verify that the schema file can be parsed as valid YAML."""
        path = get_schema_path(schema_type)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), f"Schema for {schema_type} must be a YAML mapping"
        except yaml.YAMLError as e:
            pytest.fail(f"Schema {schema_type} is not valid YAML: {e}")

    @pytest.mark.parametrize("schema_type", SCHEMA_FILES.keys())
    def test_schema_has_required_fields(self, schema_type):
        """Verify that the schema has the standard JSON Schema fields."""
        data = load_schema(schema_type)
        assert "$schema" in data or "title" in data, \
            f"Schema {schema_type} must have a $schema or title field"
        assert "properties" in data or "type" in data, \
            f"Schema {schema_type} must define properties or type"

class TestSchemaContent:
    """Tests to verify specific content requirements for each schema."""

    def test_dataset_schema_has_required_fields(self):
        """Verify dataset schema has critical fields for FR-001."""
        data = load_schema("dataset")
        required = ["issue_id", "original_code", "ground_truth_lines", "source_type"]
        props = data.get("properties", {})
        for field in required:
            assert field in props, f"Dataset schema missing required field: {field}"

    def test_agent_log_schema_has_pairing_fields(self):
        """Verify agent log schema has fields needed for T022/T023 pairing."""
        data = load_schema("agent_log")
        required = ["issue_id", "agent_type", "coverage_score", "turn_history"]
        props = data.get("properties", {})
        for field in required:
            assert field in props, f"Agent log schema missing required field: {field}"

    def test_result_schema_has_statistical_fields(self):
        """Verify result schema has fields for T031 statistical analysis."""
        data = load_schema("result")
        required = ["issue_id", "baseline_coverage", "iterative_coverage", "statistical_tests"]
        props = data.get("properties", {})
        for field in required:
            assert field in props, f"Result schema missing required field: {field}"

        # Check for association statement constraint
        assert "association_statement" in props, \
            "Result schema must include 'association_statement' for FR-007"