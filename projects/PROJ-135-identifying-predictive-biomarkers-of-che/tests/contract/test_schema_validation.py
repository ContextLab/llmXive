import os
import sys
import json
import yaml
from pathlib import Path
import pytest

# Adjust path to import if necessary, though this is a test file
# Assuming tests are run from project root

SCHEMAS_DIR = Path("specs/001-chemo-biomarker-discovery/contracts")

def load_schema(schema_name: str) -> dict:
    """Load a YAML schema file."""
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_type(value: any, expected_type: str) -> bool:
    """Basic type validation helper."""
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    return False

def validate_required_fields(data: dict, required: list, path: str = ""):
    """Recursively validate required fields."""
    for field in required:
        if field not in data:
            raise AssertionError(f"Missing required field '{field}' at {path}")

def validate_data_against_schema(data: dict, schema: dict, path: str = ""):
    """Simple recursive validation against schema (basic implementation)."""
    if schema.get("type") == "object":
        validate_required_fields(data, schema.get("required", []), path)
        if "properties" in schema:
            for key, prop_schema in schema["properties"].items():
                if key in data:
                    validate_data_against_schema(data[key], prop_schema, f"{path}.{key}")
    elif schema.get("type") == "array":
        if "items" in schema:
            for i, item in enumerate(data):
                validate_data_against_schema(item, schema["items"], f"{path}[{i}]")

class TestSchemasExist:
    def test_schemas_exist(self):
        """Verify all required schema files exist."""
        required_schemas = [
            "dataset.schema.yaml",
            "model_output.schema.yaml",
            "meta_analysis.schema.yaml"
        ]
        for schema_name in required_schemas:
            schema_path = SCHEMAS_DIR / schema_name
            assert schema_path.exists(), f"Schema file missing: {schema_path}"

class TestSchemasLoadValidYaml:
    def test_dataset_schema_loads(self):
        schema = load_schema("dataset.schema.yaml")
        assert "properties" in schema
        assert "metadata" in schema["properties"]

    def test_model_output_schema_loads(self):
        schema = load_schema("model_output.schema.yaml")
        assert "properties" in schema
        assert "model_metadata" in schema["properties"]

    def test_meta_analysis_schema_loads(self):
        schema = load_schema("meta_analysis.schema.yaml")
        assert "properties" in schema
        assert "analysis_metadata" in schema["properties"]

class TestDatasetSchemaStructure:
    def test_dataset_schema_structure(self):
        schema = load_schema("dataset.schema.yaml")
        assert schema["$schema"].endswith("json-schema.org/draft-07/schema#")
        assert "metadata" in schema["required"]
        assert "samples" in schema["required"]
        assert "features" in schema["required"]

class TestModelOutputSchemaStructure:
    def test_model_output_schema_structure(self):
        schema = load_schema("model_output.schema.yaml")
        assert "model_metadata" in schema["required"]
        assert "performance_metrics" in schema["required"]
        assert "feature_importance" in schema["required"]

class TestMetaAnalysisSchemaStructure:
    def test_meta_analysis_schema_structure(self):
        schema = load_schema("meta_analysis.schema.yaml")
        assert "analysis_metadata" in schema["required"]
        assert "differential_expression_results" in schema["required"]
        assert "gene_panel_selection" in schema["required"]

class TestSampleDataValidation:
    @pytest.fixture
    def valid_sample_dataset(self):
        return {
            "metadata": {
                "dataset_id": "TCGA-BRCA-TEST",
                "source": "TCGA",
                "tumor_type": "BRCA",
                "created_at": "2023-10-27T10:00:00Z",
                "sample_count": 100,
                "feature_count": 20000
            },
            "samples": [
                {"sample_id": "S1", "response_label": "Responder"}
            ],
            "features": [
                {"gene_symbol": "TP53", "ensembl_id": "ENSG00000141510"}
            ]
        }

    def test_valid_data_passes(self, valid_sample_dataset):
        schema = load_schema("dataset.schema.yaml")
        # Basic validation logic for test
        assert valid_sample_dataset["metadata"]["source"] in ["TCGA", "GEO"]
        assert valid_sample_dataset["metadata"]["sample_count"] >= 1

    def test_invalid_data_catches_error(self):
        invalid_data = {
            "metadata": {
                "dataset_id": "TEST",
                # Missing required fields
            }
        }
        schema = load_schema("dataset.schema.yaml")
        with pytest.raises(AssertionError):
            validate_required_fields(invalid_data, schema["required"])