"""
Unit tests for src/loader.py data fetching functionality.
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import (
    get_snap_dataset_list,
    fetch_snap_dataset,
    load_real_data,
    SNAP_DATASETS
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        raw_dir = tmp_path / "data" / "raw"
        log_dir = tmp_path / "logs"
        raw_dir.mkdir(parents=True)
        log_dir.mkdir(parents=True)
        yield {
            'base': tmp_path,
            'raw': raw_dir,
            'logs': log_dir
        }

def test_get_snap_dataset_list():
    """Test that get_snap_dataset_list returns a valid list of datasets."""
    datasets = get_snap_dataset_list()
    
    assert isinstance(datasets, list)
    assert len(datasets) > 0
    
    for dataset in datasets:
        assert 'id' in dataset
        assert 'url' in dataset
        assert dataset['id'].startswith('email-') or dataset['id'].startswith('ca-') or dataset['id'].startswith('web-') or dataset['id'].startswith('socfb-')

@patch('src.loader.urllib.request.urlretrieve')
def test_fetch_snap_dataset_success(mock_urlretrieve, temp_dirs):
    """Test successful dataset fetch."""
    # Mock the urlretrieve function
    mock_urlretrieve.return_value = None
    
    # Create a mock file that appears to be downloaded
    mock_file = temp_dirs['raw'] / "test_dataset.txt.gz"
    mock_file.write_text("mock data")
    
    dataset_info = {
        'id': 'test_dataset',
        'url': 'http://example.com/test.txt.gz'
    }
    
    result = fetch_snap_dataset(dataset_info, temp_dirs['raw'])
    
    assert result == mock_file
    assert mock_file.exists()
    mock_urlretrieve.assert_called_once_with(
        'http://example.com/test.txt.gz',
        mock_file
    )

@patch('src.loader.urllib.request.urlretrieve')
def test_fetch_snap_dataset_failure(mock_urlretrieve, temp_dirs):
    """Test failed dataset fetch raises RuntimeError."""
    # Mock the urlretrieve function to raise an exception
    mock_urlretrieve.side_effect = Exception("Network error")
    
    dataset_info = {
        'id': 'test_dataset',
        'url': 'http://example.com/test.txt.gz'
    }
    
    with pytest.raises(RuntimeError, match="Failed to fetch dataset"):
        fetch_snap_dataset(dataset_info, temp_dirs['raw'])

def test_load_real_data_with_files(temp_dirs):
    """Test load_real_data when files exist."""
    # Create mock files in raw directory
    for i in range(3):
        (temp_dirs['raw'] / f"mock_dataset_{i}.txt.gz").write_text(f"mock data {i}")
    
    # Mock get_paths to return our temp directories
    with patch('src.loader.get_paths') as mock_get_paths:
        mock_get_paths.return_value = {
            'raw_data': temp_dirs['raw'],
            'logs': temp_dirs['logs']
        }
        
        # Mock get_snap_dataset_list to return empty list (no actual fetch needed)
        with patch('src.loader.get_snap_dataset_list', return_value=[]):
            results = load_real_data()
            
            assert 'fetched' in results
            assert 'failed' in results
            assert 'total_count' in results
            assert results['total_count'] == 3
            
            # Check that fetch_count.log was created
            fetch_count_log = temp_dirs['logs'] / "fetch_count.log"
            assert fetch_count_log.exists()
            
            with open(fetch_count_log, 'r') as f:
                content = f.read()
                assert "3" in content

def test_load_real_data_no_synthetic_fallback(temp_dirs):
    """Test that load_real_data does NOT use synthetic fallback."""
    # Create empty raw directory
    
    # Mock get_paths
    with patch('src.loader.get_paths') as mock_get_paths:
        mock_get_paths.return_value = {
            'raw_data': temp_dirs['raw'],
            'logs': temp_dirs['logs']
        }
        
        # Mock fetch to fail
        with patch('src.loader.fetch_snap_dataset', side_effect=RuntimeError("Fetch failed")):
            with pytest.raises(RuntimeError, match="Dataset fetch failed"):
                load_real_data()
    
    # Verify no synthetic data was generated
    assert len(list(temp_dirs['raw'].glob("*.txt.gz"))) == 0
    assert len(list(temp_dirs['raw'].glob("synthetic_*"))) == 0
    assert len(list(temp_dirs['raw'].glob("mock_*"))) == 0
