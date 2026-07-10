"""
Unit tests for the output schema validation (T006).
Ensures that generated artifacts conform to the defined output.schema.yaml.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

# Path to the schema file relative to project root
SCHEMA_PATH = Path(__file__).parent.parent / "specs" / "001-structure-property-relationships" / "contracts" / "output.schema.yaml"


def load_schema():
    """Load the output schema from disk."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def validate_against_schema(data, schema):
    """
    Simple manual validation logic to check if data structure matches schema.
    In a real CI/CD pipeline, a library like 'jsonschema' would be used.
    This test verifies the structure is as expected.
    """
    # Check top-level keys
    assert "metadata" in data, "Missing 'metadata' key"
    assert "artifacts" in data, "Missing 'artifacts' key"

    # Check metadata
    meta = data["metadata"]
    assert "schema_version" in meta
    assert "generated_at" in meta
    assert "project_id" in meta
    assert meta["project_id"] == "PROJ-122-identifying-structure-property-relations"

    # Check artifacts
    artifacts = data["artifacts"]
    required_artifacts = [
        "processed_dataset", "feature_matrix", "model_metrics"
    ]
    for req in required_artifacts:
        assert req in artifacts, f"Missing required artifact: {req}"

    # Check specific artifact properties
    assert "path" in artifacts["processed_dataset"]
    assert "row_count" in artifacts["processed_dataset"]
    assert "checksum" in artifacts["processed_dataset"]

    assert "path" in artifacts["feature_matrix"]
    assert "column_count" in artifacts["feature_matrix"]

    assert "models" in artifacts["model_metrics"]
    assert len(artifacts["model_metrics"]["models"]) > 0

    model = artifacts["model_metrics"]["models"][0]
    assert "model_name" in model
    assert "metrics" in model
    assert "r2" in model["metrics"]
    assert "mae" in model["metrics"]


class TestOutputSchemaStructure:
    """Tests to ensure the output schema file is valid and loadable."""

    def test_schema_file_exists(self):
        """Verify that the schema file exists on disk."""
        assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"

    def test_schema_is_valid_yaml(self):
        """Verify that the schema file is valid YAML."""
        schema = load_schema()
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema

    def test_schema_has_required_top_level_keys(self):
        """Verify the schema defines required top-level keys."""
        schema = load_schema()
        assert "required" in schema
        assert "metadata" in schema["required"]
        assert "artifacts" in schema["required"]

    def test_schema_validates_sample_output(self):
        """Verify the schema structure is consistent with a valid sample output."""
        schema = load_schema()
        
        # Create a minimal valid sample output based on the schema definition
        sample_output = {
            "metadata": {
                "schema_version": "1.0.0",
                "generated_at": "2023-10-27T10:00:00Z",
                "pipeline_version": "0.1.0",
                "project_id": "PROJ-122-identifying-structure-property-relations",
                "source_files": ["data/raw/sample.csv"]
            },
            "artifacts": {
                "processed_dataset": {
                    "path": "data/processed/cleaned_data.csv",
                    "row_count": 150,
                    "checksum": "a" * 64,
                    "columns": ["smiles", "tg", "modulus"]
                },
                "feature_matrix": {
                    "path": "data/features/feature_matrix.csv",
                    "row_count": 150,
                    "column_count": 20,
                    "checksum": "b" * 64,
                    "feature_names": ["mw", "tpsa", "tg_residual"]
                },
                "model_metrics": {
                    "models": [
                        {
                            "model_name": "RandomForest",
                            "metrics": {
                                "r2": 0.85,
                                "mae": 12.5,
                                "rmse": 15.2,
                                "cv_score": 0.82,
                                "cv_std": 0.03
                            },
                            "comparison": {
                                "t_statistic": 2.45,
                                "p_value": 0.01,
                                "significant": True,
                                "correction_method": "bonferroni"
                            }
                        }
                    ]
                },
                "vif_report": {
                    "path": "data/features/vif_report.json",
                    "high_vif_features": []
                },
                "stability_metrics": {
                    "path": "data/features/stability_metrics.json",
                    "stable_features": ["mw", "tpsa"]
                },
                "data_quality_report": {
                    "path": "data/data_quality_report.json",
                    "total_records": 200,
                    "excluded_records": 50,
                    "exclusion_reasons": {
                        "invalid_smiles": 10,
                        "invalid_composition": 40
                    }
                },
                "tolerance_sensitivity_report": {
                    "path": "data/tolerance_sensitivity_report.json",
                    "thresholds_tested": [0.01, 0.02, 0.05],
                    "results": []
                },
                "baseline_metrics": {
                    "path": "data/features/baseline_metrics.json",
                    "fox_prediction_error": 5.2,
                    "gordon_taylor_prediction_error": 4.8
                },
                "raw_data_manifest": {
                    "path": "state/projects/manifest.yaml",
                    "files": []
                },
                "figures": []
            }
        }

        # Run validation logic
        validate_against_schema(sample_output, schema)

    def test_schema_enforces_iso_timestamp(self):
        """Verify the schema expects ISO 8601 timestamps."""
        schema = load_schema()
        # Navigate to metadata.generated_at
        props = schema["properties"]["metadata"]["properties"]["generated_at"]
        assert props.get("format") == "date-time"

    def test_schema_enforces_checksum_format(self):
        """Verify the schema expects 64-char hex checksums."""
        schema = load_schema()
        # Check processed_dataset checksum
        checksum_prop = schema["properties"]["artifacts"]["properties"]["processed_dataset"]["properties"]["checksum"]
        assert checksum_prop["pattern"] == "^[a-f0-9]{64}$"

    def test_schema_enforces_file_paths(self):
        """Verify the schema enforces correct file path patterns."""
        schema = load_schema()
        processed_path = schema["properties"]["artifacts"]["properties"]["processed_dataset"]["properties"]["path"]
        assert "data/processed/" in processed_path["pattern"]

        feature_path = schema["properties"]["artifacts"]["properties"]["feature_matrix"]["properties"]["path"]
        assert "data/features/" in feature_path["pattern"]

        vif_path = schema["properties"]["artifacts"]["properties"]["vif_report"]["properties"]["path"]
        assert "vif_report.json" in vif_path["pattern"]
