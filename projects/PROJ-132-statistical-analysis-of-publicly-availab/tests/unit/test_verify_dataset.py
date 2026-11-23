"""
Unit tests for src/data/verify_dataset.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure src is importable
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.verify_dataset import verify_dataset_existence


class TestVerifyDataset:
    @patch("src.data.verify_dataset.load_dataset")
    @patch("src.data.verify_dataset.LOGGER")
    def test_both_datasets_available(self, mock_logger, mock_load):
        """Test successful verification when both datasets are available."""
        # Mock eBird stream
        mock_ebird = MagicMock()
        mock_ebird.__iter__ = MagicMock(return_value=iter([{"species": "test"}]))
        mock_load.side_effect = [mock_ebird, mock_ebird] # Mock Daymet too

        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change the output path logic if needed, but here we rely on side effects
            # Since the function writes to a fixed path relative to CWD, we might need to mock open
            # or change CWD. For this test, we mock the file write.
            with patch("builtins.open"):
                result = verify_dataset_existence()

            assert result["ebird_available"] is True
            assert result["daymet_available"] is True
            mock_logger.info.assert_called()

    @patch("src.data.verify_dataset.load_dataset")
    @patch("src.data.verify_dataset.LOGGER")
    def test_ebird_missing_raises_error(self, mock_logger, mock_load):
        """Test that missing eBird dataset raises RuntimeError."""
        # Mock eBird to fail
        mock_load.side_effect = Exception("Dataset not found")

        with patch("builtins.open"):
            with pytest.raises(RuntimeError, match="eBird dataset.*missing"):
                verify_dataset_existence()

    @patch("src.data.verify_dataset.load_dataset")
    @patch("src.data.verify_dataset.LOGGER")
    def test_daymet_missing_does_not_raise(self, mock_logger, mock_load):
        """Test that missing Daymet does not raise, only logs warning."""
        # Mock eBird success
        mock_ebird = MagicMock()
        mock_ebird.__iter__ = MagicMock(return_value=iter([{"species": "test"}]))
        
        # First call (eBird) succeeds, second (Daymet) fails
        mock_load.side_effect = [mock_ebird, Exception("Daymet not found")]

        with patch("builtins.open"):
            result = verify_dataset_existence()

        assert result["ebird_available"] is True
        assert result["daymet_available"] is False
        mock_logger.warning.assert_called()