"""
Unit tests for T005a: Verify Full EBD Availability
"""
import logging
import sys
from pathlib import Path
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.verify_ebd_availability import verify_full_ebd_availability, main


class TestVerifyEBDAvailability:
    """Tests for the verify_full_ebd_availability function."""

    @patch('src.data.verify_ebd_availability.load_dataset')
    def test_dataset_not_found(self, mock_load_dataset):
        """Test that the function returns False when the dataset is not found."""
        mock_load_dataset.side_effect = Exception("Dataset not found")
        result = verify_full_ebd_availability()
        assert result is False

    @patch('src.data.verify_ebd_availability.load_dataset')
    def test_dataset_available(self, mock_load_dataset):
        """Test that the function returns True when the dataset is available."""
        mock_load_dataset.return_value = MagicMock()
        result = verify_full_ebd_availability()
        assert result is True

    @patch('src.data.verify_ebd_availability.load_dataset')
    def test_import_error(self, mock_load_dataset):
        """Test that the function returns False when there is an import error."""
        mock_load_dataset.side_effect = ImportError("No module named 'datasets'")
        result = verify_full_ebd_availability()
        assert result is False

    def test_main_execution(self, caplog):
        """Test that the main function executes without errors."""
        with caplog.at_level(logging.INFO):
            # Mock the verify function to return False to simulate unavailability
            with patch('src.data.verify_ebd_availability.verify_full_ebd_availability', return_value=False):
                main()
            # Check that the expected log message is present
            assert "Full EBD not available via verified public URL; falling back to sample scope" in caplog.text

    def test_main_execution_available(self, caplog):
        """Test that the main function executes without errors when data is available."""
        with caplog.at_level(logging.INFO):
            # Mock the verify function to return True to simulate availability
            with patch('src.data.verify_ebd_availability.verify_full_ebd_availability', return_value=True):
                main()
            # Check that the expected log message is present
            assert "Full EBD is available via a verified public URL/package." in caplog.text