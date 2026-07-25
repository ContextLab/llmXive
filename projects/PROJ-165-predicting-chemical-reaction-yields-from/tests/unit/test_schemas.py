import pytest
import yaml
import json
from pathlib import Path
import sys
import os

# Add src to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestSchemas:
    """Unit tests to verify schema files are valid YAML and follow expected structure."""

    @pytest.fixture
    def schema_dir(self):
        """Get the path to the contracts directory."""
        return Path(__file__).parent.parent.parent / "contracts"

    def test_dataset_schema_exists(self, schema_dir):
        """Verify dataset.schema.yaml exists."""
        path = schema_dir / "dataset.schema.yaml"
        assert path.exists(), f"Schema file not found: {path}"

    def test_model_output_schema_exists(self, schema_dir):
        """Verify model_output.schema.yaml exists."""
        path = schema_dir / "model_output.schema.yaml"
        assert path.exists(), f"Schema file not found: {path}"

    def test_dataset_schema_is_valid_yaml(self, schema_dir):
        """Verify dataset.schema.yaml is valid YAML."""
        path = schema_dir / "dataset.schema.yaml"
        try:
            with open(path, 'r') as f:
                schema = yaml.safe_load(f)
            assert isinstance(schema, dict), "Schema must be a dictionary"
            assert "properties" in schema, "Schema must have 'properties' at root"
            assert "metadata" in schema["properties"], "Schema must define 'metadata'"
            assert "samples" in schema["properties"], "Schema must define 'samples'"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in dataset.schema.yaml: {e}")

    def test_model_output_schema_is_valid_yaml(self, schema_dir):
        """Verify model_output.schema.yaml is valid YAML."""
        path = schema_dir / "model_output.schema.yaml"
        try:
            with open(path, 'r') as f:
                schema = yaml.safe_load(f)
            assert isinstance(schema, dict), "Schema must be a dictionary"
            assert "properties" in schema, "Schema must have 'properties' at root"
            assert "predictions" in schema["properties"], "Schema must define 'predictions'"
            assert "metrics" in schema["properties"], "Schema must define 'metrics'"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in model_output.schema.yaml: {e}")

    def test_dataset_schema_required_fields(self, schema_dir):
        """Verify dataset schema defines required fields."""
        path = schema_dir / "dataset.schema.yaml"
        with open(path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Check top-level required fields
        assert "required" in schema, "Root schema must have 'required' field"
        assert "metadata" in schema["required"], "Root schema must require 'metadata'"
        assert "samples" in schema["required"], "Root schema must require 'samples'"

    def test_model_output_schema_required_fields(self, schema_dir):
        """Verify model output schema defines required fields."""
        path = schema_dir / "model_output.schema.yaml"
        with open(path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Check top-level required fields
        assert "required" in schema, "Root schema must have 'required' field"
        assert "metadata" in schema["required"], "Root schema must require 'metadata'"
        assert "predictions" in schema["required"], "Root schema must require 'predictions'"
        assert "metrics" in schema["required"], "Root schema must require 'metrics'"

    def test_schema_references_data_model(self, schema_dir):
        """Verify schemas reference the pivot to DFT energy."""
        dataset_path = schema_dir / "dataset.schema.yaml"
        with open(dataset_path, 'r') as f:
            content = f.read()
        
        # Check for DFT energy reference in target description
        assert "DFT" in content or "energy" in content, \
            "Dataset schema should reference DFT energy as target"
        
        model_path = schema_dir / "model_output.schema.yaml"
        with open(model_path, 'r') as f:
            content = f.read()
        
        assert "DFT" in content or "energy" in content, \
            "Model output schema should reference DFT energy"