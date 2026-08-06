"""
Tests for the verify_dataset module.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.verify_dataset import verify_dataset_existence


class TestVerifyDatasetExistence:
    """Test cases for dataset verification logic."""

    @patch("src.data.verify_dataset.HfApi")
    def test_dataset_exists_via_api(self, mock_api_class):
        """Test successful verification via HfApi."""
        mock_api_instance = MagicMock()
        mock_api_class.return_value = mock_api_instance
        # Simulate success (no exception raised)
        mock_api_instance.dataset_info.return_value = MagicMock()

        result = verify_dataset_existence("test/dataset")

        assert result is True
        mock_api_instance.dataset_info.assert_called_once_with(dataset_id="test/dataset")

    @patch("src.data.verify_dataset.HfApi")
    @patch("src.data.verify_dataset.load_dataset")
    def test_dataset_exists_via_load_fallback(self, mock_load, mock_api_class):
        """Test verification falls back to load_dataset if API fails."""
        # Simulate API failure
        mock_api_instance = MagicMock()
        mock_api_class.return_value = mock_api_instance
        mock_api_instance.dataset_info.side_effect = Exception("API Error")

        # Simulate successful load
        mock_load.return_value = MagicMock()

        result = verify_dataset_existence("test/dataset")

        assert result is True
        mock_load.assert_called_once_with("test/dataset", streaming=True)

    @patch("src.data.verify_dataset.HfApi")
    @patch("src.data.verify_dataset.load_dataset")
    def test_dataset_not_found_raises_runtime_error(self, mock_load, mock_api_class):
        """Test that RuntimeError is raised if dataset is not found."""
        # Simulate API failure
        mock_api_instance = MagicMock()
        mock_api_class.return_value = mock_api_instance
        mock_api_instance.dataset_info.side_effect = Exception("API Error")

        # Simulate load failure
        mock_load.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError) as exc_info:
            verify_dataset_existence("nonexistent/dataset")

        assert "not found or inaccessible" in str(exc_info.value)