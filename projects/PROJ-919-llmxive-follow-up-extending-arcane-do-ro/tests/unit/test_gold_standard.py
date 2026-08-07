"""
Unit tests for the Gold Standard generation and validation (T009a).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

# We will test the logic by mocking the file system or checking the generated file structure
# Since the script writes to disk, we can test the schema validation logic separately
# or run the script in a temp directory.

def load_schema(schema_path: Path) -> dict:
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_annotation(ann: dict, schema: dict) -> bool:
    """Simple validator to check required fields and types based on schema."""
    required = schema.get("required", [])
    props = schema.get("properties", {})
    
    for field in required:
        if field not in ann:
            return False
        
        field_type = props.get(field, {}).get("type")
        value = ann[field]
        
        if field_type == "string" and not isinstance(value, str):
            return False
        if field_type == "number" and not isinstance(value, (int, float)):
            return False
        if field_type == "array" and not isinstance(value, list):
            return False
        
        # Check enum if present
        if "enum" in props.get(field, {}):
            if value not in props[field]["enum"]:
                return False
    
    return True

class TestGoldStandardSchema:
    @pytest.fixture
    def schema_path(self):
        # Assuming the schema is at the relative path from project root
        return Path("specs/001-gene-regulation/contracts/calibration.schema.yaml")

    def test_schema_exists(self, schema_path):
        assert schema_path.exists(), "calibration.schema.yaml must exist"

    def test_schema_valid_yaml(self, schema_path):
        schema = load_schema(schema_path)
        assert "required" in schema
        assert "properties" in schema
        assert "character" in schema["required"]
        assert "scenario" in schema["required"]
        assert "ground_truth_score" in schema["required"]
        assert "ground_truth_phase" in schema["required"]

    def test_schema_field_types(self, schema_path):
        schema = load_schema(schema_path)
        props = schema["properties"]
        
        assert props["character"]["type"] == "string"
        assert props["scenario"]["type"] == "string"
        assert props["ground_truth_score"]["type"] == "number"
        assert props["ground_truth_phase"]["type"] == "string"
        assert props["ground_truth_phase"]["enum"] == ["Coarse", "Fine", "Hybrid"]

class TestGoldStandardData:
    @pytest.fixture
    def data_path(self):
        return Path("data/gold_standard/human_annotations.json")

    def test_data_file_exists(self, data_path):
        assert data_path.exists(), "human_annotations.json must exist"

    def test_data_valid_json(self, data_path):
        with open(data_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_data_conforms_to_schema(self, data_path, schema_path):
        with open(data_path, "r") as f:
            data = json.load(f)
        
        schema = load_schema(schema_path)
        
        for item in data:
            assert validate_annotation(item, schema), f"Annotation {item} does not conform to schema"

    def test_data_has_required_fields(self, data_path):
        with open(data_path, "r") as f:
            data = json.load(f)
        
        for item in data:
            assert "character" in item
            assert "scenario" in item
            assert "ground_truth_score" in item
            assert "ground_truth_phase" in item

    def test_score_range(self, data_path):
        with open(data_path, "r") as f:
            data = json.load(f)
        
        for item in data:
            score = item["ground_truth_score"]
            assert 0.0 <= score <= 5.0, f"Score {score} out of range [0, 5]"