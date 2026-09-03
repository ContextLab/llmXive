"""
Unit tests for the streaming loader functionality.
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add the code directory to the path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from streaming_loader import (
    load_openneuro_streaming,
    save_streaming_results,
    StreamingLoaderError
)
from config import get_default_config, ensure_directories


class TestStreamingLoader:
    """Test cases for the streaming loader module."""

    @pytest.fixture
    def mock_dataset(self):
        """Create a mock dataset iterator for testing."""
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"record_id": i, "data": np.random.rand(10)}
            for i in range(10)
        ]))
        return mock_ds

    def test_load_openneuro_streaming_empty_dataset_id(self):
        """Test that empty dataset ID raises an error."""
        with pytest.raises(StreamingLoaderError, match="Dataset ID cannot be empty"):
            list(load_openneuro_streaming(""))

    @patch('streaming_loader.load_dataset')
    def test_load_openneuro_streaming_success(self, mock_load_dataset, mock_dataset):
        """Test successful streaming load."""
        mock_load_dataset.return_value = mock_dataset
        
        records = list(load_openneuro_streaming("ds0001171"))
        
        assert len(records) == 10
        assert all("record_id" in r for r in records)
        mock_load_dataset.assert_called_once_with(
            "ds0001171",
            split="train",
            streaming=True,
            cache_dir=None
        )

    @patch('streaming_loader.load_dataset')
    def test_load_openneuro_streaming_failure(self, mock_load_dataset):
        """Test that dataset fetch failure raises StreamingLoaderError."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with pytest.raises(StreamingLoaderError, match="Dataset streaming failed"):
            list(load_openneuro_streaming("ds0001171"))

    def test_save_streaming_results_creates_file(self, tmp_path):
        """Test that save_streaming_results creates the output file."""
        output_path = str(tmp_path / "results.json")
        
        save_streaming_results(
            output_path,
            "ds0001171",
            100,
            {"test_stat": 0.5}
        )
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["dataset_id"] == "ds0001171"
        assert data["processed_count"] == 100
        assert data["streaming_used"] is True
        assert data["stats"]["test_stat"] == 0.5

    def test_save_streaming_results_creates_directories(self, tmp_path):
        """Test that save_streaming_results creates parent directories."""
        output_path = str(tmp_path / "subdir" / "results.json")
        
        save_streaming_results(output_path, "ds0001171", 100)
        
        assert os.path.exists(output_path)

    def test_save_streaming_results_empty_stats(self, tmp_path):
        """Test that save_streaming_results handles None stats."""
        output_path = str(tmp_path / "results.json")
        
        save_streaming_results(output_path, "ds0001171", 100, None)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["stats"] == {}

    def test_streaming_mode_active(self, mock_dataset):
        """Test that streaming mode is properly activated."""
        with patch('streaming_loader.load_dataset', return_value=mock_dataset) as mock_load:
            list(load_openneuro_streaming("ds0001171"))
            
            # Verify streaming=True was passed
            call_kwargs = mock_load.call_args[1]
            assert call_kwargs["streaming"] is True