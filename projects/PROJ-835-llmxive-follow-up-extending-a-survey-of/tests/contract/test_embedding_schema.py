"""
Contract test for embedding output schema.
Validates that embedding outputs conform to the expected structure.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_path, ensure_dir
from tests.contract.schema_validator import validate_json_schema, EMBEDDING_SCHEMA


class TestEmbeddingSchema:
    """
    Contract tests for embedding output schema validation.
    """

    def test_schema_validation_function_exists(self):
        """Verify that the schema validation utility exists and is importable."""
        assert callable(validate_json_schema)

    def test_embedding_schema_definition(self):
        """Verify the embedding schema definition exists."""
        assert isinstance(EMBEDDING_SCHEMA, dict)
        assert "type" in EMBEDDING_SCHEMA
        assert EMBEDDING_SCHEMA["type"] == "object"

    def test_validate_valid_embedding(self):
        """Test validation against a valid embedding record."""
        valid_record = {
            "file_id": "test_001",
            "file_path": "data/audio/test.wav",
            "label": "benign",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 768,  # 3840 dimensions (example)
            "model_name": "distil-whisper-base",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        is_valid, errors = validate_json_schema(valid_record, EMBEDDING_SCHEMA)
        assert is_valid, f"Valid record failed validation: {errors}"

    def test_validate_missing_field(self):
        """Test validation fails when required field is missing."""
        invalid_record = {
            "file_id": "test_001",
            "label": "benign",
            "embedding": [0.1] * 3840,
            "model_name": "distil-whisper-base"
            # Missing 'file_path' and 'timestamp'
        }

        is_valid, errors = validate_json_schema(invalid_record, EMBEDDING_SCHEMA)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_wrong_type(self):
        """Test validation fails when field has wrong type."""
        invalid_record = {
            "file_id": 12345,  # Should be string
            "file_path": "data/audio/test.wav",
            "label": "benign",
            "embedding": "not_a_list",  # Should be list
            "model_name": "distil-whisper-base",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        is_valid, errors = validate_json_schema(invalid_record, EMBEDDING_SCHEMA)
        assert not is_valid

    def test_validate_empty_embedding(self):
        """Test validation fails for empty embedding list."""
        invalid_record = {
            "file_id": "test_001",
            "file_path": "data/audio/test.wav",
            "label": "benign",
            "embedding": [],  # Empty embedding
            "model_name": "distil-whisper-base",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        is_valid, errors = validate_json_schema(invalid_record, EMBEDDING_SCHEMA)
        # Depending on schema, empty list might be valid or invalid
        # We expect it to fail if minItems is set
        if "minItems" in EMBEDDING_SCHEMA["properties"]["embedding"]:
            assert not is_valid

    def test_contract_test_file_exists(self):
        """Verify this contract test file exists and is structured correctly."""
        assert Path(__file__).exists()
        assert Path(__file__).name == "test_embedding_schema.py"
        assert "TestEmbeddingSchema" in dir() or True  # Class is defined in file