"""
Unit tests for the verify_dataset module.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datasets import Dataset

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.verify_dataset import verify_dataset_existence, DATASET_NAME

class TestVerifyDataset:
    """Tests for the verify_dataset module."""

    @patch('src.data.verify_dataset.load_dataset')
    def test_verify_dataset_exists(self, mock_load_dataset):
        """Test that verify_dataset_existence returns True when dataset exists."""
        # Mock a successful dataset load
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds

        result = verify_dataset_existence()
        
        assert result is True
        mock_load_dataset.assert_called_once_with(DATASET_NAME, streaming=True)

    @patch('src.data.verify_dataset.load_dataset')
    def test_verify_dataset_not_found_raises_error(self, mock_load_dataset):
        """Test that verify_dataset_existence raises RuntimeError when dataset is not found."""
        # Mock a FileNotFoundError or similar
        mock_load_dataset.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError) as excinfo:
            verify_dataset_existence()
        
        assert "CRITICAL" in str(excinfo.value)
        assert DATASET_NAME in str(excinfo.value)
        assert "Critical Data Scope Note" in str(excinfo.value)

    @patch('src.data.verify_dataset.load_dataset')
    def test_verify_dataset_access_error_raises_error(self, mock_load_dataset):
        """Test that verify_dataset_existence raises RuntimeError on access errors."""
        # Mock an access error (e.g., authentication issue)
        mock_load_dataset.side_effect = Exception("Access denied")

        with pytest.raises(RuntimeError) as excinfo:
            verify_dataset_existence()
        
        assert "CRITICAL" in str(excinfo.value)
        assert "could not be found or accessed" in str(excinfo.value)