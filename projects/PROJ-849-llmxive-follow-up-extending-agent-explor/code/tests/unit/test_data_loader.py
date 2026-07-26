"""
Unit tests for the data loader module.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.lib.data_loader import (
    DataLoaderError,
    load_dataset_streaming,
    load_mathvista_streaming,
    load_scienceqa_streaming,
    get_dataset_info
)
from src.lib import config


class TestDataLoader:
    """Test cases for data loading functionality."""

    def test_load_dataset_streaming_success(self):
        """Test successful loading of a dataset with streaming."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"question": "str", "answer": "str"}

        with patch('src.lib.data_loader.load_dataset') as mock_load:
            mock_load.return_value = mock_dataset

            dataset = load_dataset_streaming(
                dataset_name="test/dataset",
                split="train",
                streaming=True
            )

            mock_load.assert_called_once_with(
                "test/dataset",
                split="train",
                streaming=True
            )
            assert dataset == mock_dataset

    def test_load_dataset_streaming_failure(self):
        """Test that DataLoaderError is raised when dataset loading fails."""
        with patch('src.lib.data_loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Dataset not found")

            with pytest.raises(DataLoaderError) as exc_info:
                load_dataset_streaming(
                    dataset_name="nonexistent/dataset",
                    split="train",
                    streaming=True
                )

            assert "Failed to load dataset" in str(exc_info.value)
            assert "nonexistent/dataset" in str(exc_info.value)

    def test_load_mathvista_streaming(self):
        """Test loading MathVista dataset."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"question": "str", "answer": "str"}

        with patch('src.lib.data_loader.load_dataset') as mock_load:
            mock_load.return_value = mock_dataset

            dataset = load_mathvista_streaming(split="train", streaming=True)

            mock_load.assert_called_once_with(
                config.MATHVISTA_DATASET_ID,
                split="train",
                streaming=True
            )
            assert dataset == mock_dataset

    def test_load_scienceqa_streaming(self):
        """Test loading ScienceQA dataset."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"question": "str", "answer": "str"}

        with patch('src.lib.data_loader.load_dataset') as mock_load:
            mock_load.return_value = mock_dataset

            dataset = load_scienceqa_streaming(split="train", streaming=True)

            mock_load.assert_called_once_with(
                config.SCIENCEQA_DATASET_ID,
                split="train",
                streaming=True
            )
            assert dataset == mock_dataset

    def test_get_dataset_info(self):
        """Test extracting dataset information."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"question": "str", "answer": "str"}
        mock_dataset.num_columns = 2
        mock_dataset.num_rows = 1000

        info = get_dataset_info(mock_dataset)

        assert info["type"] == "MagicMock"
        assert info["features"] == ["question", "answer"]
        assert info["num_examples"] == 1000

    def test_get_dataset_info_streaming(self):
        """Test extracting dataset info for streaming dataset."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"question": "str", "answer": "str"}
        # Streaming datasets don't have num_rows
        del mock_dataset.num_rows

        info = get_dataset_info(mock_dataset)

        assert info["type"] == "MagicMock"
        assert info["features"] == ["question", "answer"]
        assert "num_examples" not in info or info["num_examples"] is None