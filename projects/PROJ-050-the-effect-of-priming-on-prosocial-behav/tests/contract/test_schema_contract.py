"""Contract tests for schema validation interface."""
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml

from code.utils.schema_validator import (
    load_schema,
    validate_schema,
    validate_dataset_schema,
    validate_scored_schema,
    validate_output_schema,
)


class TestSchemaContract:
    """Test suite for schema validation contract."""

    def test_load_schema_returns_dict(self):
        """Test that load_schema returns a dictionary."""
        # Create a temporary schema file
        schema = {
            "name": "test_schema",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "text", "type": "string"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
          schema_file = Path(tmp_dir) / "schema.yaml"
          with open(schema_file, "w") as f:
              yaml.dump(schema, f)

          result = load_schema(str(schema_file))
          assert isinstance(result, dict)
          assert result["name"] == "test_schema"

    def test_validate_schema_accepts_valid_schema(self):
        """Test that validate_schema accepts a valid schema."""
        schema = {
            "name": "valid_schema",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "text", "type": "string"},
            ],
        }

        is_valid, errors = validate_schema(schema)
        assert is_valid
        assert len(errors) == 0

    def test_validate_schema_rejects_invalid_schema(self):
        """Test that validate_schema rejects an invalid schema."""
        # Missing required 'columns' field
        schema = {"name": "invalid_schema"}

        is_valid, errors = validate_schema(schema)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_dataset_schema_with_real_data(self):
        """Test validate_dataset_schema with a DataFrame matching the expected schema."""
        # Create a DataFrame matching the dataset schema
        df = pd.DataFrame({
            "comment_id": [1, 2, 3],
            "thread_id": [1, 1, 2],
            "thread_type": ["Prime", "Control", "Prime"],
            "text": ["Text 1", "Text 2", "Text 3"],
            "user_id": ["hash1", "hash2", "hash3"],
            "subreddit": ["sub1", "sub2", "sub3"],
        })

        is_valid, errors = validate_dataset_schema(df)
        assert is_valid, f"Validation failed: {errors}"

    def test_validate_scored_schema_with_real_data(self):
        """Test validate_scored_schema with a DataFrame matching the scored schema."""
        # Create a DataFrame matching the scored schema
        df = pd.DataFrame({
            "comment_id": [1, 2, 3],
            "neg_score": [0.1, 0.2, 0.3],
            "prosocial_action_count": [1, 0, 2],
            "thread_type": ["Prime", "Control", "Prime"],
        })

        is_valid, errors = validate_scored_schema(df)
        assert is_valid, f"Validation failed: {errors}"

    def test_validate_output_schema_with_real_data(self):
        """Test validate_output_schema with a DataFrame matching the output schema."""
        # Create a DataFrame matching the output schema
        df = pd.DataFrame({
            "comment_id": [1, 2, 3],
            "thread_type": ["Prime", "Control", "Prime"],
            "neg_score": [0.1, 0.2, 0.3],
            "prosocial_action_count": [1, 0, 2],
            "coefficient": [0.5, 0.5, 0.5],
            "p_value": [0.01, 0.02, 0.03],
        })

        is_valid, errors = validate_output_schema(df)
        assert is_valid, f"Validation failed: {errors}"