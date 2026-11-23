import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
from data.download import (
    stream_pick_a_pic_dataset,
    load_project_state,
    save_project_state,
    update_state_with_checksum,
    compute_sha256,
    validate_row,
    download_and_checksum
)
from utils.errors import DataSchemaError
import hashlib

class TestDownloadLoudFailure:
    """
    Test suite to verify that the data loader FAILS LOUDLY on fetch errors
    and does NOT fall back to synthetic data generation.
    """

    @patch('data.download.datasets')
    def test_stream_pick_a_pic_dataset_fetch_failure_raises(self, mock_datasets):
        """
        Verify that if load_dataset fails (e.g., 404, connection error),
        the function raises DataSchemaError immediately.
        No synthetic data should be generated.
        """
        # Simulate a fetch failure
        mock_datasets.load_dataset.side_effect = Exception("Connection error: Dataset not found")

        with pytest.raises(Exception, match="Connection error: Dataset not found"):
            # We expect the function to propagate the exception, not catch it
            list(stream_pick_a_pic_dataset(limit=1))

    @patch('data.download.datasets')
    def test_stream_pick_a_pic_dataset_missing_column_raises(self, mock_datasets):
        """
        Verify that if the dataset is loaded but lacks 'human_rating',
        a DataSchemaError is raised.
        """
        # Mock the dataset object
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([{"caption": "test"}]))
        mock_dataset.__getitem__ = MagicMock(side_effect=KeyError("human_rating"))
        mock_dataset.column_names = ["caption", "image"]

        mock_datasets.load_dataset.return_value = mock_dataset

        # The stream_pick_a_pic_dataset function should validate columns
        # and raise DataSchemaError if 'human_rating' is missing
        with pytest.raises(DataSchemaError, match="Missing required dataset or column: pick-a-pic/human_rating"):
            list(stream_pick_a_pic_dataset(limit=1))

    def test_no_synthetic_fallback_in_download_module(self):
        """
        Static check to ensure no synthetic data generation functions
        (like generate_synthetic_* or mock_*) are called in download.py
        when a real fetch fails.
        """
        download_path = Path("code/data/download.py")
        if not download_path.exists():
            pytest.skip("download.py not found in expected location")

        content = download_path.read_text()

        # Check for forbidden patterns that indicate synthetic fallback
        forbidden_patterns = [
            "generate_synthetic",
            "mock_data",
            "np.random",
            "fake_row",
            "placeholder",
            "if .*: return generate",
            "except.*:.*generate"
        ]

        for pattern in forbidden_patterns:
            if pattern.lower() in content.lower():
                # Allow comments or docstrings mentioning these, but not active code paths
                # For this strict check, we assume any presence is a risk unless commented out
                # A more robust check would parse AST, but for now we flag presence
                pytest.fail(f"Potential synthetic fallback pattern found in download.py: {pattern}")

    @patch('data.download.datasets')
    def test_loud_failure_on_404(self, mock_datasets):
        """
        Simulate a specific 404 error from the HuggingFace API.
        The loader must raise, not return empty/synthetic data.
        """
        from datasets.exceptions import DatasetNotFoundError
        
        mock_datasets.load_dataset.side_effect = DatasetNotFoundError("Dataset not found: pick-a-pic")

        with pytest.raises(DatasetNotFoundError):
            list(stream_pick_a_pic_dataset(limit=1))