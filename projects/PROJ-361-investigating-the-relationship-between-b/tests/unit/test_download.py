"""
Unit tests for download_openneuro.py schema validation and error handling.

This test suite verifies:
1. FileNotFoundError is raised if the dataset_description.json path is missing.
2. ValueError is raised if the 'id' field is missing from the JSON.
3. RuntimeError is raised with the specific message "Real data fetch failed" 
   if the OpenNeuro API returns a 404 error.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path for imports if running from tests/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_utils import DataFetchError
from preprocessing.download_openneuro import validate_dataset_schema, fetch_dataset_metadata


class TestDatasetSchemaValidation:
    """Tests for validate_dataset_schema function."""

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised if path is missing."""
        non_existent_path = Path("/tmp/does_not_exist/dataset_description.json")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            validate_dataset_schema(non_existent_path)
        
        assert "dataset_description.json" in str(exc_info.value)

    def test_missing_id_field(self):
        """Test that ValueError is raised if 'id' field is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"Name": "Test Dataset", "BIDSVersion": "1.8.0"}, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                validate_dataset_schema(temp_path)
            
            assert "Missing required field 'id'" in str(exc_info.value)
        finally:
            temp_path.unlink()

    def test_valid_schema(self):
        """Test that valid schema passes without error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "Name": "Test Dataset", 
                "BIDSVersion": "1.8.0",
                "id": "ds001234"
            }, f)
            temp_path = Path(f.name)

        try:
            # Should not raise
            result = validate_dataset_schema(temp_path)
            assert result == "ds001234"
        finally:
            temp_path.unlink()


class TestRealDataFetch:
    """Tests for fetch_dataset_metadata and error handling."""

    @patch('requests.get')
    def test_api_404_raises_runtime_error(self, mock_get):
        """Test that a 404 from OpenNeuro API raises RuntimeError with specific message."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Client Error")
        mock_get.return_value = mock_response

        # We expect the function to raise RuntimeError with the specific message
        # The download_openneuro.py should catch the HTTP error and re-raise as RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            fetch_dataset_metadata("ds_nonexistent")
        
        assert str(exc_info.value) == "Real data fetch failed"

    @patch('requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful metadata fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ds004285",
            "name": "Visual Illusions Study",
            "version": "1.0.0"
        }
        mock_get.return_value = mock_response

        result = fetch_dataset_metadata("ds004285")
        
        assert result["id"] == "ds004285"
        assert result["name"] == "Visual Illusions Study"
        mock_get.assert_called_once()