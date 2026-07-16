"""
Unit tests for src/utils/io.py

Tests verify that fetch_text, load_ratings, and validate_schemas
correctly load data and raise appropriate exceptions for missing/invalid files.
"""

import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to adjust the import path because the test is running from code/tests/unit
# but the module is at code/src/utils/io.py
import sys
from pathlib import Path

# Add the code directory to the path
code_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_root))

from src.utils.io import (
    fetch_text,
    load_ratings,
    validate_schemas,
    RATINGS_FILE,
    CONVERSATIONS_FILE,
    RATINGS_REQUIRED_COLUMNS
)


class TestValidateSchemas:
    def test_validate_schemas_ratings_missing_file(self):
        """Test that validate_schemas raises FileNotFoundError if ratings.csv is missing."""
        with patch('src.utils.io.RATINGS_FILE', MagicMock(exist=False)) as mock_file:
            mock_file.exists.return_value = False
            with pytest.raises(FileNotFoundError) as exc_info:
                validate_schemas(file_type="ratings")
            assert "Phase 0" in str(exc_info.value)

    def test_validate_schemas_ratings_wrong_columns(self):
        """Test that validate_schemas raises ValueError if columns are missing."""
        df = pd.DataFrame({"wrong_col": [1, 2, 3]})
        with pytest.raises(ValueError) as exc_info:
            validate_schemas(df, file_type="ratings")
        assert "Schema mismatch" in str(exc_info.value)
        assert "conversation_id" in str(exc_info.value)

    def test_validate_schemas_ratings_valid(self):
        """Test that validate_schemas passes for valid ratings DataFrame."""
        df = pd.DataFrame({
            "conversation_id": ["1", "2"],
            "authenticity_score": [4.0, 3.5],
            "rater_id": ["r1", "r2"],
            "timestamp": ["2023-01-01", "2023-01-02"]
        })
        # Should not raise
        validate_schemas(df, file_type="ratings")

    def test_validate_schemas_conversations_missing_file(self):
        """Test that validate_schemas raises FileNotFoundError if conversations.jsonl is missing."""
        with patch('src.utils.io.CONVERSATIONS_FILE', MagicMock(exist=False)) as mock_file:
            mock_file.exists.return_value = False
            with pytest.raises(FileNotFoundError):
                validate_schemas(file_type="conversations")

    def test_validate_schemas_conversations_wrong_columns(self):
        """Test that validate_schemas raises ValueError for conversations with wrong columns."""
        df = pd.DataFrame({"text_only": ["hello"]})
        with pytest.raises(ValueError) as exc_info:
            validate_schemas(df, file_type="conversations")
        assert "conversation_id" in str(exc_info.value)


class TestLoadRatings:
    @patch('src.utils.io.RATINGS_FILE')
    def test_load_ratings_file_not_found(self, mock_file):
        """Test load_ratings raises FileNotFoundError when file is missing."""
        mock_file.exists.return_value = False
        with pytest.raises(FileNotFoundError) as exc_info:
            load_ratings()
        assert "Phase 0" in str(exc_info.value)

    @patch('src.utils.io.pd.read_csv')
    @patch('src.utils.io.RATINGS_FILE')
    def test_load_ratings_empty_file(self, mock_file, mock_read_csv):
        """Test load_ratings raises ValueError for empty file."""
        mock_file.exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame()
        with pytest.raises(ValueError) as exc_info:
            load_ratings()
        assert "empty" in str(exc_info.value).lower()

    @patch('src.utils.io.pd.read_csv')
    @patch('src.utils.io.RATINGS_FILE')
    def test_load_ratings_success(self, mock_file, mock_read_csv):
        """Test load_ratings returns DataFrame with valid data."""
        mock_file.exists.return_value = True
        expected_df = pd.DataFrame({
            "conversation_id": ["1"],
            "authenticity_score": [5.0],
            "rater_id": ["r1"],
            "timestamp": ["2023-01-01"]
        })
        mock_read_csv.return_value = expected_df

        result = load_ratings()
        pd.testing.assert_frame_equal(result, expected_df)


class TestFetchText:
    @patch('src.utils.io.CONVERSATIONS_FILE')
    def test_fetch_text_file_not_found(self, mock_file):
        """Test fetch_text raises FileNotFoundError when file is missing."""
        mock_file.exists.return_value = False
        with pytest.raises(FileNotFoundError) as exc_info:
            fetch_text()
        assert "Phase 0" in str(exc_info.value) or "data acquisition" in str(exc_info.value)

    @patch('src.utils.io.pd.read_json')
    @patch('src.utils.io.CONVERSATIONS_FILE')
    def test_fetch_text_empty_file(self, mock_file, mock_read_json):
        """Test fetch_text raises ValueError for empty file."""
        mock_file.exists.return_value = True
        mock_read_json.return_value = pd.DataFrame()
        with pytest.raises(ValueError) as exc_info:
            fetch_text()
        assert "empty" in str(exc_info.value).lower()

    @patch('src.utils.io.pd.read_json')
    @patch('src.utils.io.CONVERSATIONS_FILE')
    def test_fetch_text_missing_columns(self, mock_file, mock_read_json):
        """Test fetch_text raises ValueError for missing columns."""
        mock_file.exists.return_value = True
        mock_read_json.return_value = pd.DataFrame({"wrong_col": ["text"]})
        with pytest.raises(ValueError) as exc_info:
            fetch_text()
        assert "conversation_id" in str(exc_info.value)

    @patch('src.utils.io.pd.read_json')
    @patch('src.utils.io.CONVERSATIONS_FILE')
    def test_fetch_text_success(self, mock_file, mock_read_json):
        """Test fetch_text returns DataFrame with valid data."""
        mock_file.exists.return_value = True
        expected_df = pd.DataFrame({
            "conversation_id": ["1"],
            "text_content": ["Hello world"]
        })
        mock_read_json.return_value = expected_df

        result = fetch_text()
        pd.testing.assert_frame_equal(result, expected_df)