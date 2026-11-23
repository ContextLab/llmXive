"""
Unit tests for schema validation logic.
Verifies that validate_dataframe raises on malformed data.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.data_validation import load_schema, validate_dataframe, validate_row


class TestSchemaValidation:
    """Tests for schema validation logic."""

    @pytest.fixture
    def valid_schema(self):
        """Load the interaction schema."""
        schema_path = Path("contracts/interaction_schema.schema.yaml")
        return load_schema(schema_path)

    @pytest.fixture
    def valid_dataframe(self, valid_schema):
        """Create a DataFrame that matches the schema."""
        return pd.DataFrame({
            "post_text": ["Valid post 1", "Valid post 2"],
            "reply_text": ["Valid reply 1", "Valid reply 2"],
            "timestamp": ["2023-01-01T12:00:00", "2023-01-02T13:00:00"],
            "user_id": ["user_001", "user_002"]
        })

    def test_valid_dataframe_passes(self, valid_dataframe):
        """Test that a valid DataFrame does not raise."""
        # Should not raise any exception
        result = validate_dataframe(valid_dataframe)
        assert result is True

    def test_missing_required_column_raises(self):
        """Test that missing a required column raises ValidationError."""
        df = pd.DataFrame({
            "post_text": ["Valid post"],
            "reply_text": ["Valid reply"],
            "timestamp": ["2023-01-01T12:00:00"]
            # Missing 'user_id'
        })

        with pytest.raises(ValueError, match="Missing required columns"):
            validate_dataframe(df)

    def test_wrong_type_column_raises(self):
        """Test that a column with wrong type raises ValueError."""
        df = pd.DataFrame({
            "post_text": ["Valid post"],
            "reply_text": ["Valid reply"],
            "timestamp": ["2023-01-01T12:00:00"],
            "user_id": [12345]  # Should be string, not int
        })

        with pytest.raises(ValueError, match="Column 'user_id' has invalid type"):
            validate_dataframe(df)

    def test_empty_dataframe_raises(self):
        """Test that an empty DataFrame raises ValueError."""
        df = pd.DataFrame(columns=["post_text", "reply_text", "timestamp", "user_id"])

        with pytest.raises(ValueError, match="DataFrame is empty"):
            validate_dataframe(df)

    def test_null_values_in_required_field_raises(self):
        """Test that null values in required fields raise ValueError."""
        df = pd.DataFrame({
            "post_text": [None, "Valid post"],
            "reply_text": ["Valid reply", "Valid reply"],
            "timestamp": ["2023-01-01T12:00:00", "2023-01-02T13:00:00"],
            "user_id": ["user_001", "user_002"]
        })

        with pytest.raises(ValueError, match="Column 'post_text' contains null values"):
            validate_dataframe(df)

    def test_validate_row_valid(self, valid_schema):
        """Test that a valid row passes validation."""
        row = {
            "post_text": "Test post",
            "reply_text": "Test reply",
            "timestamp": "2023-01-01T12:00:00",
            "user_id": "user_001"
        }
        result = validate_row(row, valid_schema)
        assert result is True

    def test_validate_row_missing_field(self, valid_schema):
        """Test that a row missing a field raises ValueError."""
        row = {
            "post_text": "Test post",
            "reply_text": "Test reply",
            "timestamp": "2023-01-01T12:00:00"
            # Missing 'user_id'
        }
        with pytest.raises(ValueError, match="Missing required field"):
            validate_row(row, valid_schema)