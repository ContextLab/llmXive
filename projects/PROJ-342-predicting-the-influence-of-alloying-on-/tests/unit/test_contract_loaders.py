"""
Unit tests for schema loaders.
"""
import json
import tempfile
from pathlib import Path

import pytest
import yaml

from code.contracts.schema_loader import (
    DatasetSchemaLoader,
    ArtifactSchemaLoader,
    SchemaValidationError,
)


# Helper to create temporary schema files
def create_temp_schema(schema_dict: dict) -> Path:
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with open(fd, "w", encoding="utf-8") as f:
        yaml.dump(schema_dict, f)
    return Path(path)


# Helper to create temporary data files
def create_temp_data(data_dict: dict) -> Path:
    fd, path = tempfile.mkstemp(suffix=".json")
    with open(fd, "w", encoding="utf-8") as f:
        json.dump(data_dict, f)
    return Path(path)


class TestDatasetSchemaLoader:
    def test_valid_dataset(self):
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "temperature": {"type": "number", "minimum": 0},
                "composition": {"type": "string"},
            },
            "required": ["id", "temperature"],
        }
        schema_path = create_temp_schema(schema)
        loader = DatasetSchemaLoader(schema_path)

        data = {"id": "mg-001", "temperature": 500.5, "composition": "Zr41Ti14"}
        # Should not raise
        loader.validate(data)
        schema_path.unlink()

    def test_missing_required_field(self):
        schema = {
            "type": "object",
            "properties": {"id": {"type": "string"}, "value": {"type": "number"}},
            "required": ["id", "value"],
        }
        schema_path = create_temp_schema(schema)
        loader = DatasetSchemaLoader(schema_path)

        data = {"id": "mg-001"}  # Missing 'value'
        with pytest.raises(SchemaValidationError) as exc_info:
            loader.validate(data)

        assert "Missing required field: value" in str(exc_info.value)
        schema_path.unlink()

    def test_invalid_type(self):
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        schema_path = create_temp_schema(schema)
        loader = DatasetSchemaLoader(schema_path)

        data = {"count": "not_a_number"}
        with pytest.raises(SchemaValidationError) as exc_info:
            loader.validate(data)

        assert "invalid type" in str(exc_info.value)
        schema_path.unlink()

    def test_value_below_minimum(self):
        schema = {
            "type": "object",
            "properties": {"temp": {"type": "number", "minimum": 0}},
            "required": ["temp"],
        }
        schema_path = create_temp_schema(schema)
        loader = DatasetSchemaLoader(schema_path)

        data = {"temp": -10}
        with pytest.raises(SchemaValidationError) as exc_info:
            loader.validate(data)

        assert "below minimum" in str(exc_info.value)
        schema_path.unlink()


class TestArtifactSchemaLoader:
    def test_valid_single_artifact(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "metric": {"type": "number"},
            },
            "required": ["name"],
        }
        schema_path = create_temp_schema(schema)
        loader = ArtifactSchemaLoader(schema_path)

        data = {"name": "model_v1", "metric": 0.95}
        loader.validate(data)  # Should not raise
        schema_path.unlink()

    def test_valid_list_of_artifacts(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "score": {"type": "number"},
            },
            "required": ["name"],
        }
        schema_path = create_temp_schema(schema)
        loader = ArtifactSchemaLoader(schema_path)

        data = [
            {"name": "model_a", "score": 0.8},
            {"name": "model_b", "score": 0.9},
        ]
        loader.validate(data)  # Should not raise
        schema_path.unlink()

    def test_invalid_type_in_list(self):
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        schema_path = create_temp_schema(schema)
        loader = ArtifactSchemaLoader(schema_path)

        data = [
            {"count": 10},
            {"count": "invalid"},
        ]
        with pytest.raises(SchemaValidationError) as exc_info:
            loader.validate(data)

        assert "Record 1" in str(exc_info.value)
        schema_path.unlink()

    def test_non_dict_in_list(self):
        schema = {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        }
        schema_path = create_temp_schema(schema)
        loader = ArtifactSchemaLoader(schema_path)

        data = [{"id": "a"}, "not_a_dict"]
        with pytest.raises(SchemaValidationError) as exc_info:
            loader.validate(data)

        assert "Record 1 is not a dictionary" in str(exc_info.value)
        schema_path.unlink()
