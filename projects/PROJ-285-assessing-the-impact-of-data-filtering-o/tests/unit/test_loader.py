"""
Unit tests for the chunked loader module (code/src/loader.py).
"""
import pytest
import pandas as pd
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.loader import _get_memory_usage_bytes, _log_memory_usage, MAX_MEMORY_GB

class TestMemoryUtils:
    def test_get_memory_usage_bytes_returns_positive(self):
        mem = _get_memory_usage_bytes()
        assert mem > 0
        assert isinstance(mem, int)

    def test_log_memory_usage_creates_file(self, tmp_path, monkeypatch):
        # Mock the path to use a temp directory
        profile_path = tmp_path / "memory_profile.csv"
        monkeypatch.setattr("src.loader.MEMORY_PROFILE_PATH", profile_path)
        
        _log_memory_usage("test_step", 1024, 1024)
        
        assert profile_path.exists()
        with open(profile_path, 'r') as f:
            content = f.read()
            assert "test_step" in content
            assert "current_gb" in content
            assert "peak_gb" in content

class TestChunkedLoader:
    @patch('src.loader.load_dataset')
    def test_load_slfc_dataset_chunked_streaming(self, mock_load_dataset):
        # Mock the dataset object
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        
        # Mock the streaming iterator
        mock_iterator = [
            {"id": 1, "ra": 10.0, "dec": 20.0, "snr": 5.5},
            {"id": 2, "ra": 11.0, "dec": 21.0, "snr": 6.0},
            {"id": 3, "ra": 12.0, "dec": 22.0, "snr": 7.5},
            {"id": 4, "ra": 13.0, "dec": 23.0, "snr": 8.0},
        ]
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_iterator))
        
        from src.loader import load_slfc_dataset_chunked
        
        chunks = list(load_slfc_dataset_chunked(chunk_size=2))
        
        assert len(chunks) == 2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 2
        assert chunks[0]["id"].tolist() == [1, 2]
        assert chunks[1]["id"].tolist() == [3, 4]

    @patch('src.loader.load_dataset')
    def test_load_slfc_dataset_chunked_column_filtering(self, mock_load_dataset):
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        
        mock_iterator = [
            {"id": 1, "ra": 10.0, "dec": 20.0, "snr": 5.5, "extra": "a"},
            {"id": 2, "ra": 11.0, "dec": 21.0, "snr": 6.0, "extra": "b"},
        ]
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_iterator))
        
        from src.loader import load_slfc_dataset_chunked
        
        chunks = list(load_slfc_dataset_chunked(chunk_size=2, columns=["id", "snr"]))
        
        assert len(chunks) == 1
        assert list(chunks[0].columns) == ["id", "snr"]
        assert "extra" not in chunks[0].columns
        assert "dec" not in chunks[0].columns

    @patch('src.loader.load_dataset')
    def test_load_slfc_dataset_chunked_handles_remaining_rows(self, mock_load_dataset):
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        
        # 5 rows, chunk size 2 -> expect 3 chunks (2, 2, 1)
        mock_iterator = [
            {"id": i} for i in range(1, 6)
        ]
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_iterator))
        
        from src.loader import load_slfc_dataset_chunked
        
        chunks = list(load_slfc_dataset_chunked(chunk_size=2))
        
        assert len(chunks) == 3
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 2
        assert len(chunks[2]) == 1