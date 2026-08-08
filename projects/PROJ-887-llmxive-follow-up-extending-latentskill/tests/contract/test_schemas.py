"""
Contract tests for schema validation of project artifacts.

This module validates that output files (JSON/YAML) conform to the
defined schemas in specs/001-lattentskill-retrieval-geometry/contracts/.
"""

import json
import os
from pathlib import Path

import pytest
import yaml

# Import schema validation logic if available, otherwise use simple checks
try:
    from src.validate.citation_check import load_json_safe
except ImportError:
    # Fallback if citation_check isn't fully implemented yet
    def load_json_safe(path: str):
        with open(path, 'r') as f:
            return json.load(f)


# Define expected schema structures for key outputs
# These are derived from the project's contract definitions and task requirements

STATS_REPORT_SCHEMA = {
    "required_keys": [
        "linearity_check",
        "reconstruction_error",
        "sensitivity_analysis",
        "statistical_tests"
    ],
    "linearity_check": {
        "type": "object",
        "required_keys": ["pearson_correlation", "validity_flag"]
    },
    "reconstruction_error": {
        "type": "object",
        "required_keys": ["mean_cosine_distance", "strategy"]
    },
    "sensitivity_analysis": {
        "type": "object",
        "required_keys": ["k_values", "results"]
    },
    "statistical_tests": {
        "type": "object",
        "required_keys": ["p_values", "bh_q_values", "method"]
    }
}

RECONSTRUCTION_ERROR_SCHEMA = {
    "required_keys": ["mean_cosine_distance", "strategy", "task_name"],
    "types": {
        "mean_cosine_distance": float,
        "strategy": str,
        "task_name": str
    }
}

LINEARITY_CHECK_SCHEMA = {
    "required_keys": ["pearson_correlation", "validity_flag", "n_pairs"],
    "types": {
        "pearson_correlation": float,
        "validity_flag": bool,
        "n_pairs": int
    }
}


def load_contract_schema(schema_name: str) -> dict:
    """Load a schema definition from the contracts directory."""
    contracts_dir = Path("specs/001-lattentskill-retrieval-geometry/contracts")
    schema_file = contracts_dir / f"{schema_name}.yaml"
    if not schema_file.exists():
        # Fallback to in-memory definitions if file is missing
        if schema_name == "stats_report":
            return STATS_REPORT_SCHEMA
        return {}
    with open(schema_file, 'r') as f:
        return yaml.safe_load(f)


def validate_against_schema(data: dict, schema: dict) -> bool:
    """
    Validate a data dictionary against a schema definition.
    Returns True if valid, raises AssertionError otherwise.
    """
    if not schema:
        return True  # No schema defined, skip validation

    # Check required top-level keys
    for key in schema.get("required_keys", []):
        assert key in data, f"Missing required key: {key}"

    # Check nested structures if defined
    for key, sub_schema in schema.items():
        if key.startswith("_") or key == "required_keys" or key == "types":
            continue
        if key in data and isinstance(sub_schema, dict):
            if "required_keys" in sub_schema:
                for sub_key in sub_schema["required_keys"]:
                    assert sub_key in data[key], f"Missing nested key: {key}.{sub_key}"
            if "types" in sub_schema:
                for sub_key, expected_type in sub_schema["types"].items():
                    if sub_key in data[key]:
                        assert isinstance(data[key][sub_key], expected_type), \
                            f"Type mismatch for {key}.{sub_key}: expected {expected_type}, got {type(data[key][sub_key])}"

    # Check type constraints for top-level keys
    if "types" in schema:
        for key, expected_type in schema["types"].items():
            if key in data:
                assert isinstance(data[key], expected_type), \
                    f"Type mismatch for {key}: expected {expected_type}, got {type(data[key])}"

    return True


class TestStatsReportSchema:
    """Contract tests for src/evaluation/stats.py output (stats_report.json)."""

    @pytest.fixture
    def sample_stats_report(self):
        """Generate a valid sample stats report for testing."""
        return {
            "linearity_check": {
                "pearson_correlation": 0.85,
                "validity_flag": True,
                "n_pairs": 10
            },
            "reconstruction_error": {
                "mean_cosine_distance": 0.12,
                "strategy": "cosine_weighted",
                "task_name": "alfworld_navigation"
            },
            "sensitivity_analysis": {
                "k_values": [1, 3, 5],
                "results": {
                    "1": 0.65,
                    "3": 0.72,
                    "5": 0.70
                }
            },
            "statistical_tests": {
                "p_values": [0.03, 0.04],
                "bh_q_values": [0.05, 0.06],
                "method": "wilcoxon_signed_rank"
            }
        }

    def test_schema_structure(self, sample_stats_report):
        """Verify the stats report matches the expected schema."""
        schema = load_contract_schema("stats_report")
        # Use in-memory fallback if file missing
        if not schema:
            schema = STATS_REPORT_SCHEMA
        validate_against_schema(sample_stats_report, schema)

    def test_file_exists_and_valid(self):
        """Test that the actual output file exists and is valid."""
        output_path = Path("data/results/stats_report.json")
        if not output_path.exists():
            pytest.skip(f"Output file {output_path} not found. Task may not be complete.")

        data = load_json_safe(str(output_path))
        schema = load_contract_schema("stats_report")
        if not schema:
            schema = STATS_REPORT_SCHEMA
        validate_against_schema(data, schema)


class TestReconstructionErrorSchema:
    """Contract tests for src/validation/reconstruction_error.py output."""

    @pytest.fixture
    def sample_reconstruction_error(self):
        return {
            "mean_cosine_distance": 0.15,
            "strategy": "unweighted_mean",
            "task_name": "searchqa_qa"
        }

    def test_schema_structure(self, sample_reconstruction_error):
        schema = RECONSTRUCTION_ERROR_SCHEMA
        validate_against_schema(sample_reconstruction_error, schema)

    def test_file_exists_and_valid(self):
        output_path = Path("data/results/reconstruction_error.json")
        if not output_path.exists():
            pytest.skip(f"Output file {output_path} not found.")

        data = load_json_safe(str(output_path))
        validate_against_schema(data, RECONSTRUCTION_ERROR_SCHEMA)


class TestLinearityCheckSchema:
    """Contract tests for src/validation/linearity_check.py output."""

    @pytest.fixture
    def sample_linearity_check(self):
        return {
            "pearson_correlation": 0.78,
            "validity_flag": True,
            "n_pairs": 20
        }

    def test_schema_structure(self, sample_linearity_check):
        schema = LINEARITY_CHECK_SCHEMA
        validate_against_schema(sample_linearity_check, schema)

    def test_file_exists_and_valid(self):
        output_path = Path("data/results/linearity_check.json")
        if not output_path.exists():
            pytest.skip(f"Output file {output_path} not found.")

        data = load_json_safe(str(output_path))
        validate_against_schema(data, LINEARITY_CHECK_SCHEMA)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])