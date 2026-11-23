"""
Contract tests for data and output schema validation.
"""
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import load_schema, validate_artifact

class TestSchemaValidation:
    """Contract tests for schema validation."""

    def test_load_dataset_schema(self):
        """Test that the dataset schema can be loaded and is valid."""
        schema_path = Path(__file__).parent.parent.parent / "specs" / "001-structure-property-relationships" / "contracts" / "dataset.schema.yaml"
        if schema_path.exists():
            schema = load_schema(str(schema_path))
            assert schema is not None
            assert "type" in schema or "properties" in schema

    def test_load_output_schema(self):
        """Test that the output schema can be loaded and is valid."""
        schema_path = Path(__file__).parent.parent.parent / "specs" / "001-structure-property-relationships" / "contracts" / "output.schema.yaml"
        if schema_path.exists():
            schema = load_schema(str(schema_path))
            assert schema is not None
