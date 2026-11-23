"""
Tests for data fetch error handling.

These tests verify that the data loading functions raise errors
when fetching fails, rather than falling back to synthetic data.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from data.fetch_utils import DataFetchError, load_real_dataset, validate_dataset_structure
from pathlib import Path
import tempfile


class TestDataFetchErrorHandling:
    """Test cases for data fetch error handling."""

    def test_load_real_dataset_raises_on_failure(self):
        """Test that load_real_dataset raises DataFetchError on failure."""
        with patch("data.fetch_utils.load_dataset") as mock_load:
            mock_load.side_effect = Exception("Connection refused")

            with pytest.raises(DataFetchError, match="Failed to load real dataset"):
                load_real_dataset("fake/dataset")

    def test_load_real_dataset_raises_no_synthetic_fallback(self):
        """Test that no synthetic data is returned on failure."""
        with patch("data.fetch_utils.load_dataset") as mock_load:
            mock_load.side_effect = Exception("Dataset not found")

            # Should raise, not return synthetic data
            with pytest.raises(DataFetchError):
                load_real_dataset("nonexistent/dataset")

    def test_validate_dataset_structure_raises_on_missing_fields(self):
        """Test validation raises when required fields are missing."""
        # Create a mock dataset with missing fields
        mock_dataset = MagicMock()
        mock_dataset.features = {"id": "int", "text": "string"}  # Missing 'label'

        with pytest.raises(DataFetchError, match="Missing required field"):
            validate_dataset_structure(
                mock_dataset,
                required_fields=["id", "text", "label"],
                min_examples=0
            )

    def test_validate_dataset_structure_raises_on_low_count(self):
        """Test validation raises when example count is too low."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"id": "int"}
        mock_dataset.__iter__ = MagicMock(return_value=iter([{"id": 1}, {"id": 2}]))

        with pytest.raises(DataFetchError, match="minimum required"):
            validate_dataset_structure(
                mock_dataset,
                required_fields=["id"],
                min_examples=10
            )

    def test_data_fetch_error_is_exception(self):
        """Test that DataFetchError is a proper exception."""
        try:
            raise DataFetchError("Test error")
        except Exception as e:
            assert isinstance(e, DataFetchError)
            assert "Test error" in str(e)

    def test_load_real_dataset_with_token_from_env(self):
        """Test that token is read from environment variable."""
        with patch("data.fetch_utils.load_dataset") as mock_load:
            mock_load.return_value = MagicMock()

            with patch.dict(os.environ, {"HF_TOKEN": "test_token_123"}):
                load_real_dataset("some/dataset")

            # Verify token was passed
            call_kwargs = mock_load.call_args.kwargs
            assert call_kwargs.get("token") == "test_token_123"
