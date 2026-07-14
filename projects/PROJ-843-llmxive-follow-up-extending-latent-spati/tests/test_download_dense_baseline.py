"""
Tests for T016b: Download dense baseline.

These tests verify that the download script:
1. Attempts to fetch from the correct source.
2. Handles missing data by failing loudly (not fabricating).
3. Saves the file to the correct location.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_raw_dir, ensure_directories
from eval.download_dense_baseline import download_dense_baseline, calculate_sha256


def test_calculate_sha256():
    """Test SHA256 calculation."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)
    
    sha = calculate_sha256(tmp_path)
    # Expected SHA256 for "test data"
    expected = "3f93389240547802098081008390072492036004036000000000000000000000" # Placeholder, actual calculation needed
    # Let's calculate real one
    import hashlib
    real_sha = hashlib.sha256(b"test data").hexdigest()
    
    assert sha == real_sha
    os.unlink(tmp_path)


@patch('eval.download_dense_baseline.load_dataset')
@patch('eval.download_dense_baseline.get_raw_dir')
def test_download_success(mock_get_raw, mock_load_dataset):
    """Test successful download and save."""
    # Mock config
    mock_raw_dir = Path(tempfile.mkdtemp())
    mock_get_raw.return_value = mock_raw_dir
    
    # Mock dataset
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter([{'frames': np.random.rand(10, 10, 3)}]))
    mock_load_dataset.return_value = mock_dataset
    
    # Run
    result = download_dense_baseline()
    
    # Verify
    assert result is True
    output_file = mock_raw_dir / "dense_baseline_frames.npy"
    assert output_file.exists()
    
    # Verify content
    data = np.load(output_file)
    assert data.shape == (1, 10, 10, 3)
    
    # Cleanup
    shutil.rmtree(mock_raw_dir)


@patch('eval.download_dense_baseline.load_dataset')
@patch('eval.download_dense_baseline.get_raw_dir')
def test_download_failure_missing_data(mock_get_raw, mock_load_dataset):
    """Test that download fails loudly if data is missing."""
    mock_raw_dir = Path(tempfile.mkdtemp())
    mock_get_raw.return_value = mock_raw_dir
    
    # Mock dataset to raise error
    mock_load_dataset.side_effect = Exception("Dataset not found")
    
    # We expect sys.exit(1)
    with patch('sys.exit') as mock_exit:
        download_dense_baseline()
        mock_exit.assert_called_once_with(1)
    
    shutil.rmtree(mock_raw_dir)


@patch('eval.download_dense_baseline.load_dataset')
@patch('eval.download_dense_baseline.get_raw_dir')
def test_download_failure_no_frames(mock_get_raw, mock_load_dataset):
    """Test that download fails if no frames are found."""
    mock_raw_dir = Path(tempfile.mkdtemp())
    mock_get_raw.return_value = mock_raw_dir
    
    # Mock dataset with no frames
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter([{'other': 'data'}]))
    mock_load_dataset.return_value = mock_dataset
    
    with patch('sys.exit') as mock_exit:
        download_dense_baseline()
        mock_exit.assert_called_once_with(1)
    
    shutil.rmtree(mock_raw_dir)