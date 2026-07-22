import pytest
import yaml
import json
from pathlib import Path
import sys
import os

# Add project root to path if necessary
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestSchemas:
    """Unit tests to verify the validity and structure of contract schemas."""

    @pytest.fixture
    def contracts_dir(self):
        return Path(__file__).parent.parent.parent / "contracts"

    def test_dataset_schema_exists(self, contracts_dir):
        """Verify that the dataset schema file exists."""
        schema_path = contracts_dir / "dataset.schema.yaml"
        assert schema_path.exists(), f"Dataset schema file not found at {schema_path}"

    def test_model_output_schema_exists(self, contracts_dir):
        """Verify that the model output schema file exists."""
        schema_path = contracts_dir / "model_output.schema.yaml"
        assert schema_path.exists(), f"Model output schema file not found at {schema_path}"

    def test_dataset_schema_is_valid_yaml(self, contracts_dir):
        """Verify that the dataset schema is valid YAML."""
        schema_path = contracts_dir / "dataset.schema.yaml"
        try:
            with open(schema_path, 'r') as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), "Parsed dataset schema is not a dictionary"
            assert "dataset" in data, "Missing 'dataset' key in schema"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in dataset schema: {e}")

    def test_model_output_schema_is_valid_yaml(self, contracts_dir):
        """Verify that the model output schema is valid YAML."""
        schema_path = contracts_dir / "model_output.schema.yaml"
        try:
            with open(schema_path, 'r') as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), "Parsed model output schema is not a dictionary"
            assert "model_output" in data, "Missing 'model_output' key in schema"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in model output schema: {e}")

    def test_dataset_schema_has_required_fields(self, contracts_dir):
        """Verify that the dataset schema contains required top-level fields."""
        schema_path = contracts_dir / "dataset.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        dataset_def = data.get("dataset", {})
        assert "type" in dataset_def, "Missing 'type' in dataset schema"
        assert dataset_def["type"] == "object", "Dataset schema type must be 'object'"
        assert "required" in dataset_def, "Missing 'required' fields in dataset schema"
        assert "samples" in dataset_def["required"], "Missing 'samples' in required fields"
        assert "metadata" in dataset_def["required"], "Missing 'metadata' in required fields"

    def test_model_output_schema_has_required_fields(self, contracts_dir):
        """Verify that the model output schema contains required top-level fields."""
        schema_path = contracts_dir / "model_output.schema.yaml"
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)

        output_def = data.get("model_output", {})
        assert "type" in output_def, "Missing 'type' in model output schema"
        assert output_def["type"] == "object", "Model output schema type must be 'object'"
        assert "required" in output_def, "Missing 'required' fields in model output schema"
        required_fields = output_def["required"]
        assert "metadata" in required_fields, "Missing 'metadata' in required fields"
        assert "predictions" in required_fields, "Missing 'predictions' in required fields"
        assert "metrics" in required_fields, "Missing 'metrics' in required fields"

    def test_target_variable_reflects_pivot(self, contracts_dir):
        """Verify that the schema reflects the pivot to DFT energy."""
        dataset_path = contracts_dir / "dataset.schema.yaml"
        with open(dataset_path, 'r') as f:
            data = yaml.safe_load(f)

        # Check description mentions DFT energy
        desc = data.get("description", "")
        assert "DFT" in desc or "energy" in desc.lower(), \
            "Dataset schema description should mention DFT energy pivot"

        # Check sample properties for target_energy
        samples_props = data["dataset"]["properties"]["samples"]["items"]["properties"]
        assert "target_energy" in samples_props, \
            "Missing 'target_energy' in sample properties"
        assert "normalized_dft_total_molecular_energy" in samples_props["target_energy"].get(
            "description", ""
        ).lower() or "dft" in samples_props["target_energy"].get("description", "").lower(), \
            "target_energy description should reference DFT energy"
