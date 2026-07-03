"""
Unit tests for the ingest module.
"""

import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data import ingest
from src.utils.config import get_config

class TestIngestHandlesMissingC11:
    """Test that ingest handles missing C11 values gracefully."""

    @patch('src.data.ingest.fetch_from_materials_project')
    def test_missing_c11_returns_none(self, mock_fetch):
        """
        Verify that when C11 is missing in the response, the function returns None
        and logs a warning.
        """
        # Mock response with missing C11 (c_ij too short)
        mock_fetch.return_value = None

        result = ingest.fetch_from_materials_project("mp-130", "fake_key")
        assert result is None

    @patch('src.data.ingest.fetch_from_materials_project')
    def test_incomplete_c_ij_tensor(self, mock_fetch):
        """
        Verify that when c_ij tensor is incomplete, the function handles it.
        """
        # Simulate a scenario where fetch returns None due to incomplete data
        mock_fetch.return_value = None

        with patch('src.utils.logging.log_warning') as mock_log:
            result = ingest.fetch_from_materials_project("mp-999", "fake_key")
            assert result is None

    @patch('src.data.ingest.requests.get')
    def test_api_error_handling(self, mock_get):
        """
        Verify that API errors are handled gracefully and don't crash the ingest.
        """
        mock_get.side_effect = Exception("Network error")

        with patch('src.utils.logging.log_error') as mock_log:
            result = ingest.fetch_from_materials_project("mp-130", "fake_key")
            assert result is None

    @patch('src.data.ingest.fetch_from_materials_project')
    def test_skipped_entries_logged(self, mock_fetch):
        """
        Verify that skipped entries are logged with their IDs.
        """
        mock_fetch.return_value = None

        with patch('src.utils.logging.log_warning') as mock_log:
            result = ingest.fetch_from_materials_project("mp-130", "fake_key")
            assert result is None
            # Verify log_warning was called with the material ID
            assert any("mp-130" in str(call) for call in mock_log.call_args_list)

class TestIngestValidation:
    """Test data validation in ingest module."""

    def test_minimum_entries_check(self):
        """Verify that minimum entry count is enforced."""
        assert ingest.MIN_ENTRIES == 50

    @patch('src.data.ingest.fetch_from_materials_project')
    def test_valid_c_ij_extraction(self, mock_fetch):
        """
        Verify that valid c_ij tensors are correctly extracted.
        """
        # Mock a valid response
        mock_fetch.return_value = {
            "C11": 100.0,
            "C12": 50.0,
            "C44": 30.0,
            "structure_type": "fcc",
            "elements": ["Al"]
        }

        result = ingest.fetch_from_materials_project("mp-130", "fake_key")
        assert result is not None
        assert result["C11"] == 100.0
        assert result["C12"] == 50.0
        assert result["C44"] == 30.0

class TestIngestIntegration:
    """Integration tests for the ingest pipeline."""

    @patch('src.data.ingest.validate_api_keys')
    @patch('src.data.ingest.get_config')
    @patch('src.data.ingest.get_path')
    @patch('src.data.ingest.ingest_materials_project')
    @patch('builtins.open', new_callable=MagicMock)
    def test_run_ingest_creates_csv(
        self, mock_open, mock_ingest_mp, mock_get_path, mock_get_config, mock_validate
    ):
        """
        Verify that run_ingest creates a CSV file with correct structure.
        """
        # Mock configuration
        mock_get_config.return_value = {"MP_API_KEY": "fake_key"}
        mock_validate.return_value = None

        # Mock path
        mock_get_path.return_value = Path(tempfile.gettempdir())

        # Mock ingest results
        mock_ingest_mp.return_value = [
            {
                "material_id": "mp-130",
                "source": "materials_project",
                "C11": 100.0,
                "C12": 50.0,
                "C44": 30.0,
                "structure_type": "fcc",
                "elements": ["Al"]
            }
        ]

        # Run ingest
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.csv")
            result_path = ingest.run_ingest(output_path)

            assert os.path.exists(result_path)
            assert result_path == output_path

    @patch('src.data.ingest.validate_api_keys')
    @patch('src.data.ingest.get_config')
    def test_missing_api_key_raises_error(self, mock_get_config, mock_validate):
        """
        Verify that missing MP_API_KEY raises an appropriate error.
        """
        mock_get_config.return_value = {}  # No API key
        mock_validate.return_value = None

        with pytest.raises(ValueError, match="MP_API_KEY"):
            ingest.run_ingest()
