import os
import sys
import yaml
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

class TestDataSchema:
    """Contract tests for data schema validation."""

    def test_dataset_schema_exists(self):
        """Test that the dataset schema file exists."""
        schema_path = project_root / "specs" / "001-gene-regulation" / "contracts" / "dataset_schema.schema.yaml"
        assert schema_path.exists(), f"Dataset schema not found at {schema_path}"

    def test_output_schema_exists(self):
        """Test that the output schema file exists."""
        schema_path = project_root / "specs" / "001-gene-regulation" / "contracts" / "output_schema.schema.yaml"
        assert schema_path.exists(), f"Output schema not found at {schema_path}"

    def test_dataset_schema_valid_yaml(self):
        """Test that the dataset schema is valid YAML."""
        schema_path = project_root / "specs" / "001-gene-regulation" / "contracts" / "dataset_schema.schema.yaml"
        with open(schema_path, 'r') as f:
            try:
                schema = yaml.safe_load(f)
                assert schema is not None
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in dataset schema: {e}")

    def test_output_schema_valid_yaml(self):
        """Test that the output schema is valid YAML."""
        schema_path = project_root / "specs" / "001-gene-regulation" / "contracts" / "output_schema.schema.yaml"
        with open(schema_path, 'r') as f:
            try:
                schema = yaml.safe_load(f)
                assert schema is not None
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in output schema: {e}")

    def test_dataset_schema_has_required_properties(self):
        """Test that the dataset schema has required top-level properties."""
        schema_path = project_root / "specs" / "001-gene-regulation" / "contracts" / "dataset_schema.schema.yaml"
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        assert "properties" in schema
        assert "metadata" in schema["properties"]
        assert "counts_matrix" in schema["properties"]

    def test_output_schema_has_required_properties(self):
        """Test that the output schema has required top-level properties."""
        schema_path = project_root / "specs" / "001-gene-regulation" / "contracts" / "output_schema.schema.yaml"
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        assert "properties" in schema
        assert "predictions" in schema["properties"]
        assert "metrics" in schema["properties"]
        assert "model_info" in schema["properties"]