"""
Unit tests for download_meg.py
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Add src to path if not already present
sys_path = str(Path(__file__).parent.parent.parent / "code")
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from src.data.download_meg import download_meg_streamed


@patch('src.data.download_meg.load_dataset')
def test_download_meg_streamed_creates_file(mock_load_dataset):
    """Test that download_meg_streamed creates a parquet file"""
    # Mock dataset iterator
    mock_dataset = iter([
        {"subject": "01", "channel": "MEG0111", "value": 1.5},
        {"subject": "01", "channel": "MEG0112", "value": 2.3},
        {"subject": "02", "channel": "MEG0111", "value": 1.8},
    ] * 500)  # 1500 rows total

    mock_load_dataset.return_value = mock_dataset

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = download_meg_streamed(tmp_dir)

        # Check file exists
        assert os.path.exists(output_file)

        # Check file is valid parquet
        df = pd.read_parquet(output_file)
        assert len(df) > 1000
        assert "subject" in df.columns
        assert "channel" in df.columns
        assert "value" in df.columns


@patch('src.data.download_meg.load_dataset')
def test_download_meg_streamed_empty_dataset(mock_load_dataset):
    """Test behavior with empty dataset"""
    mock_dataset = iter([])
    mock_load_dataset.return_value = mock_dataset

    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception):
            # Empty dataset should raise an error or handle gracefully
            # depending on implementation requirements
            download_meg_streamed(tmp_dir)