"""
Contract tests for validating benchmark output against results.schema.yaml.

This module ensures that the pipeline output strictly adheres to the defined
JSON Schema, preventing regression in result formats and ensuring downstream
consumers can reliably parse the data.
"""
import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict

import yaml

# Import the schema loader from utils to ensure consistency
# Note: We assume the schema file is at the expected relative path
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "results.schema.yaml"
RESULTS_PATH = Path(__file__).parent.parent.parent / "data" / "results" / "final_benchmark_report.json"

# Fallback path if results are in a different location (e.g. processed)
FALLBACK_RESULTS_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "access_control_results.json"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and return the JSON schema."""
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate data against a JSON schema using the jsonschema library.
    Raises AssertionError if validation fails.
    """
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema library not installed. Install with: pip install jsonschema")

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Data validation failed: {e.message} at path {list(e.path)}")


class TestResultsSchema:
    """Contract tests for the results schema."""

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the results schema."""
        return load_schema(SCHEMA_PATH)

    @pytest.fixture
    def sample_results(self, schema) -> Dict[str, Any]:
        """
        Generate a minimal valid sample results object based on the schema.
        This is used for positive testing.
        """
        return {
            "metadata": {
                "timestamp": "2023-10-27T10:00:00Z",
                "pipeline_version": "1.0.0",
                "dataset_version": "gatemem-v1",
                "domains": ["medical", "office"],
                "config": {"seed": 42}
            },
            "access_control": {
                "gatekeeper": {
                    "unauthorized_exposure_rate": 0.05,
                    "true_positive_rate": 0.95,
                    "false_positive_rate": 0.02,
                    "sample_size": 100
                },
                "baseline": {
                    "unauthorized_exposure_rate": 0.20,
                    "true_positive_rate": 0.98,
                    "false_positive_rate": 0.01,
                    "sample_size": 100
                },
                "comparison": {
                    "absolute_reduction": 0.15,
                    "relative_reduction_pct": 75.0,
                    "significance_test": {
                        "method": "paired_ttest",
                        "statistic": 2.5,
                        "p_value": 0.01,
                        "significant": True
                    }
                }
            },
            "utility": {
                "gatekeeper": {
                    "overall_success_rate": 0.90,
                    "conditional_utility": 0.92,
                    "sample_size": 100
                },
                "baseline": {
                    "overall_success_rate": 0.91,
                    "conditional_utility": 0.93,
                    "sample_size": 100
                },
                "comparison": {
                    "absolute_difference": -0.01,
                    "relative_change_pct": -1.1,
                    "significance_test": {
                        "method": "wilcoxon",
                        "statistic": 10.0,
                        "p_value": 0.45,
                        "significant": False
                    }
                }
            },
            "forgetting": {
                "gatekeeper": {
                    "deletion_compliance_rate": 0.99,
                    "sample_size": 50
                },
                "baseline": {
                    "deletion_compliance_rate": 0.10,
                    "sample_size": 50
                },
                "comparison": {
                    "absolute_difference": 0.89,
                    "significance_test": {
                        "method": "lmm",
                        "statistic": 5.2,
                        "p_value": 0.001,
                        "significant": True
                    }
                }
            },
            "performance": {
                "gatekeeper": {
                    "avg_latency_ms": 150.5,
                    "peak_ram_mb": 1200.0,
                    "sample_size": 100
                },
                "baseline": {
                    "avg_latency_ms": 500.0,
                    "peak_ram_mb": 3500.0,
                    "sample_size": 100
                },
                "comparison": {
                    "latency_reduction_pct": 70.0,
                    "ram_reduction_pct": 65.7
                }
            },
            "statistical_analysis": {
                "primary_method": "lmm",
                "fallback_method": "paired_ttest",
                "domain_stratified": [
                    {
                        "domain": "medical",
                        "method_used": "paired_ttest",
                        "statistic": 2.1,
                        "p_value": 0.04,
                        "significant": True
                    }
                ]
            }
        }

    def test_schema_file_exists(self):
        """Verify that the schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

    def test_schema_is_valid_yaml(self, schema):
        """Verify the schema is valid YAML and parses correctly."""
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema

    def test_sample_data_validates(self, schema, sample_results):
        """Verify that a correctly structured sample validates against the schema."""
        validate_against_schema(sample_results, schema)

    def test_missing_required_top_level_keys(self, schema, sample_results):
        """Verify that missing required top-level keys cause validation failure."""
        del sample_results["metadata"]
        with pytest.raises(AssertionError) as exc_info:
            validate_against_schema(sample_results, schema)
        assert "metadata" in str(exc_info.value)

    def test_invalid_metric_value_type(self, schema, sample_results):
        """Verify that wrong types (e.g., string instead of number) fail validation."""
        sample_results["access_control"]["gatekeeper"]["unauthorized_exposure_rate"] = "0.05"
        with pytest.raises(AssertionError) as exc_info:
            validate_against_schema(sample_results, schema)
        assert "unauthorized_exposure_rate" in str(exc_info.value)

    def test_out_of_range_value(self, schema, sample_results):
        """Verify that values outside [0, 1] for rates fail validation."""
        sample_results["access_control"]["gatekeeper"]["unauthorized_exposure_rate"] = 1.5
        with pytest.raises(AssertionError) as exc_info:
            validate_against_schema(sample_results, schema)
        assert "1.5" in str(exc_info.value) or "maximum" in str(exc_info.value).lower()

    def test_missing_domain_stratified_entry(self, schema, sample_results):
        """Verify that missing required fields in domain_stratified fail validation."""
        sample_results["statistical_analysis"]["domain_stratified"][0].pop("p_value")
        with pytest.raises(AssertionError) as exc_info:
            validate_against_schema(sample_results, schema)
        assert "p_value" in str(exc_info.value)

    def test_real_output_validation(self, schema):
        """
        Attempt to validate the real output file if it exists.
        If the file doesn't exist, this test is skipped (not failed).
        """
        target_path = RESULTS_PATH if RESULTS_PATH.exists() else FALLBACK_RESULTS_PATH

        if not target_path.exists():
            pytest.skip(f"Real output file not found at {RESULTS_PATH} or {FALLBACK_RESULTS_PATH}. "
                        "Run the pipeline to generate results before running this test.")

        with open(target_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Real output file is not valid JSON: {e}")

        validate_against_schema(data, schema)
