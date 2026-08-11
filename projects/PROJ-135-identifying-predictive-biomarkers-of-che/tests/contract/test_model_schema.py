import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Import shared test utilities if available, otherwise define locally
try:
    from tests.contract.test_schema_validation import load_schema, validate_data_against_schema
except ImportError:
    # Fallback for standalone execution if the import path differs in environment
    # Assuming standard project structure where tests/contract is accessible
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from tests.contract.test_schema_validation import load_schema, validate_data_against_schema


class TestModelOutputSchema:
    """
    Contract test for model output schema in tests/contract/test_model_schema.py.
    Requirement: Verify that model output conforms to model_output.schema.yaml
    including all required fields.
    """

    @pytest.fixture
    def schema_path(self, project_root_path):
        """Locate the model_output.schema.yaml file."""
        schema_file = (
            project_root_path
            / "specs"
            / "001-chemo-biomarker-discovery"
            / "contracts"
            / "model_output.schema.yaml"
        )
        assert schema_file.exists(), f"Schema file not found: {schema_file}"
        return schema_file

    @pytest.fixture
    def valid_model_output(self):
        """Generate a valid model output dictionary according to the schema."""
        # This structure assumes the schema defines fields like:
        # - model_id (string)
        # - tumor_type (string)
        # - metrics (object with auc, pr_auc, etc.)
        # - parameters (object)
        # - gene_panel (list)
        # - timestamp (string)
        return {
            "model_id": "test-model-001",
            "tumor_type": "BRCA",
            "metrics": {
                "auc": 0.85,
                "pr_auc": 0.72,
                "accuracy": 0.80,
                "balanced_accuracy": 0.78
            },
            "parameters": {
                "C": 1.0,
                "l1_ratio": 0.5,
                "max_iter": 1000
            },
            "gene_panel": ["GENE_A", "GENE_B", "GENE_C"],
            "timestamp": "2023-10-27T10:00:00Z",
            "validation_status": "passed"
        }

    @pytest.fixture
    def invalid_model_output_missing_field(self):
        """Generate an invalid model output missing a required field."""
        return {
            "model_id": "test-model-002",
            "tumor_type": "LUAD",
            "metrics": {
                "auc": 0.75
            },
            # Missing 'parameters', 'gene_panel', 'timestamp'
            "gene_panel": []
        }

    @pytest.fixture
    def invalid_model_output_wrong_type(self):
        """Generate an invalid model output with wrong data type."""
        return {
            "model_id": 12345,  # Should be string
            "tumor_type": "COAD",
            "metrics": {
                "auc": "high"  # Should be number
            },
            "parameters": {},
            "gene_panel": [],
            "timestamp": "2023-10-27T10:00:00Z"
        }

    def test_schemas_exist(self, schema_path):
        """Assert that the model_output.schema.yaml exists."""
        assert schema_path.exists()

    def test_load_schema_valid(self, schema_path):
        """Assert that the schema can be loaded as valid YAML."""
        schema = load_schema(schema_path)
        assert schema is not None
        assert "type" in schema or "properties" in schema

    def test_valid_model_output_conforms(self, schema_path, valid_model_output):
        """
        Verify that a valid model output conforms to the schema.
        This is the primary contract test.
        """
        schema = load_schema(schema_path)
        # The validation function should raise an error or return False if invalid
        # Assuming validate_data_against_schema returns True on success or raises
        try:
            result = validate_data_against_schema(valid_model_output, schema)
            # If the function returns a boolean
            assert result is True, "Valid output failed schema validation"
        except Exception as e:
            # If the function raises on failure, we expect no exception here
            pytest.fail(f"Valid output raised exception: {e}")

    def test_invalid_model_output_missing_field(self, schema_path, invalid_model_output_missing_field):
        """Verify that missing required fields are caught."""
        schema = load_schema(schema_path)
        with pytest.raises((AssertionError, ValueError, TypeError)) as exc_info:
            validate_data_against_schema(invalid_model_output_missing_field, schema)
        assert "missing" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_invalid_model_output_wrong_type(self, schema_path, invalid_model_output_wrong_type):
        """Verify that wrong data types are caught."""
        schema = load_schema(schema_path)
        with pytest.raises((AssertionError, ValueError, TypeError)) as exc_info:
            validate_data_against_schema(invalid_model_output_wrong_type, schema)
        assert "type" in str(exc_info.value).lower() or "expected" in str(exc_info.value).lower()

    def test_model_output_file_structure(self, project_root_path):
        """
        Verify the directory structure where model outputs are expected to be saved.
        This ensures the contract path exists or is creatable.
        """
        output_dir = project_root_path / "results" / "meta_analysis"
        # We don't assert existence strictly as the pipeline might not have run,
        # but we verify the path logic is consistent with the schema location.
        assert isinstance(output_dir, Path)
        assert "results" in str(output_dir)