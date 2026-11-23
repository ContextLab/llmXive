"""
Unit tests for utils.py functions.
"""
import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

from utils import (
    SchemaValidationError,
    load_json_file,
    save_json_file,
    load_csv_file,
    save_csv_file,
    load_schema,
    validate_against_schema,
    validate_schema,
    is_valid_uuid4,
    load_config_schema,
    load_drift_result_schema,
    validate_drift_result_schema,
    load_taxonomy_mapping_file,
    save_taxonomy_mapping_file,
    load_centroids_file,
    save_centroids_file,
    load_drift_scores_file,
    save_drift_scores_file,
    load_ground_truth_fixture,
    save_ground_truth_fixture,
)
from config import get_path


class TestJsonFileIO:
    def test_load_json_file(self, tmp_path):
        """Test loading a JSON file."""
        data = {"key": "value", "number": 42}
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)

        loaded = load_json_file(file_path)
        assert loaded == data

    def test_save_json_file(self, tmp_path):
        """Test saving a JSON file."""
        data = {"key": "value", "number": 42}
        file_path = tmp_path / "test.json"

        save_json_file(file_path, data)
        with open(file_path, 'r') as f:
            loaded = json.load(f)

        assert loaded == data


class TestCsvFileIO:
    def test_load_csv_file(self, tmp_path):
        """Test loading a CSV file."""
        data = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"}
        ]
        file_path = tmp_path / "test.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name"])
            writer.writeheader()
            writer.writerows(data)

        loaded = load_csv_file(file_path)
        assert len(loaded) == 2
        assert loaded[0]["id"] == "1"
        assert loaded[0]["name"] == "Alice"

    def test_save_csv_file(self, tmp_path):
        """Test saving a CSV file."""
        data = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"}
        ]
        file_path = tmp_path / "test.csv"

        save_csv_file(file_path, data)
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            loaded = list(reader)

        assert len(loaded) == 2
        assert loaded[0]["id"] == "1"
        assert loaded[0]["name"] == "Alice"

    def test_save_csv_file_empty(self, tmp_path):
        """Test saving an empty CSV file."""
        data = []
        file_path = tmp_path / "test.csv"
        save_csv_file(file_path, data)
        assert file_path.exists()
        assert file_path.stat().st_size == 0


class TestSchemaValidation:
    def test_validate_against_schema_valid(self):
        """Test validation with a valid schema."""
        schema = {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"}
            }
        }
        data = {"id": "123", "name": "Test"}
        assert validate_against_schema(data, schema) is True

    def test_validate_against_schema_missing_required(self):
        """Test validation with missing required field."""
        schema = {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"}
            }
        }
        data = {"id": "123"}
        with pytest.raises(SchemaValidationError, match="Missing required field"):
            validate_against_schema(data, schema)

    def test_validate_against_schema_wrong_type(self):
        """Test validation with wrong type."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"}
            }
        }
        data = {"id": 123}
        with pytest.raises(SchemaValidationError, match="expected string"):
            validate_against_schema(data, schema)

    def test_validate_schema(self, tmp_path):
        """Test validate_schema function."""
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string"}
            }
        }
        schema_path = tmp_path / "schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema, f)

        data = {"id": "123"}
        assert validate_schema(data, schema_path) is True

        bad_data = {"id": 123}
        with pytest.raises(SchemaValidationError):
            validate_schema(bad_data, schema_path)


class TestUuidValidation:
    def test_is_valid_uuid4_valid(self):
        """Test valid UUID4."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        assert is_valid_uuid4(uuid_str) is True

    def test_is_valid_uuid4_invalid(self):
        """Test invalid UUID4."""
        uuid_str = "not-a-uuid"
        assert is_valid_uuid4(uuid_str) is False

    def test_is_valid_uuid4_wrong_version(self):
        """Test UUID with wrong version."""
        uuid_str = "550e8400-e29b-31d4-a716-446655440000"  # version 3
        assert is_valid_uuid4(uuid_str) is False


class TestSpecificLoaders:
    def test_is_valid_uuid4_edge_cases(self):
        """Test edge cases for UUID validation."""
        # Valid UUID4
        assert is_valid_uuid4("6ba7b810-9dad-11d1-80b4-00c04fd430c8") is False  # version 1
        assert is_valid_uuid4("6ba7b811-9dad-11d1-80b4-00c04fd430c8") is False  # version 1
        assert is_valid_uuid4("f47ac10b-58cc-4372-a567-0e02b2c3d479") is True  # version 4
        assert is_valid_uuid4("F47AC10B-58CC-4372-A567-0E02B2C3D479") is True  # uppercase

    def test_save_load_taxonomy_mapping(self, tmp_path):
        """Test saving and loading taxonomy mapping."""
        data = {"category": "safety", "items": ["item1", "item2"]}
        file_path = tmp_path / "taxonomy.json"

        save_taxonomy_mapping_file(data, file_path)
        loaded = load_taxonomy_mapping_file(file_path)

        assert loaded == data

    def test_save_load_centroids(self, tmp_path):
        """Test saving and loading centroids."""
        data = {"centroid_1": [0.1, 0.2], "centroid_2": [0.3, 0.4]}
        file_path = tmp_path / "centroids.json"

        save_centroids_file(data, file_path)
        loaded = load_centroids_file(file_path)

        assert loaded == data

    def test_save_load_ground_truth(self, tmp_path):
        """Test saving and loading ground truth."""
        data = [
            {"log_id": "1", "text": "test", "label": "benign"},
            {"log_id": "2", "text": "test2", "label": "novel"}
        ]
        file_path = tmp_path / "ground_truth.json"

        save_ground_truth_fixture(data, file_path)
        loaded = load_ground_truth_fixture(file_path)

        assert len(loaded) == 2
        assert loaded[0]["label"] == "benign"
        assert loaded[1]["label"] == "novel"

    def test_save_load_drift_scores(self, tmp_path):
        """Test saving and loading drift scores."""
        data = [
            {"log_id": "1", "drift_score": 0.5, "review_flag": False},
            {"log_id": "2", "drift_score": 0.9, "review_flag": True}
        ]
        file_path = tmp_path / "drift_scores.csv"

        save_drift_scores_file(data, file_path)
        loaded = load_drift_scores_file(file_path)

        assert len(loaded) == 2
        assert float(loaded[0]["drift_score"]) == 0.5
        assert loaded[0]["review_flag"] == "False"  # CSV stores as string
        assert loaded[1]["review_flag"] == "True"
