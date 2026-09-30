import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import load_real_data, get_snap_dataset_list, fetch_snap_dataset

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_dir = tmp_path / "data" / "raw"
        state_dir = tmp_path / "state"
        results_dir = tmp_path / "results"
        raw_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        
        config = {
            "paths": {
                "raw_data": str(raw_dir),
                "state": str(state_dir),
                "results": str(results_dir)
            }
        }
        yield config, raw_dir, state_dir, results_dir

def test_get_snap_dataset_list():
    """Test that get_snap_dataset_list returns a non-empty list."""
    datasets = get_snap_dataset_list()
    assert isinstance(datasets, list)
    assert len(datasets) > 0
    # Check that some known SNAP datasets are present
    known_datasets = {"ca-AstrPH", "email-Enron", "web-Google"}
    assert any(d in known_datasets for d in datasets), "Expected known SNAP datasets in the list"

def test_load_real_data_with_insufficient_files(temp_dirs):
    """
    Test load_real_data when file count < 10.
    It should:
    1. Set regression_blocked: True in state/data_availability.yaml
    2. Generate results/descriptive_stats.json with mean, median, std_dev
    3. NOT generate synthetic data
    """
    config, raw_dir, state_dir, results_dir = temp_dirs
    
    # Create fewer than 10 dummy files
    for i in range(5):
        (raw_dir / f"dummy_{i}.edges.gz").touch()
    
    with patch('src.loader.fetch_snap_dataset', return_value=None): # Simulate no new fetches
        result = load_real_data(config)
    
    # Check return value
    assert result['file_count'] == 5
    assert result['regression_blocked'] is True
    assert result['descriptive_stats'] is not None
    
    # Check state file
    state_file = state_dir / "data_availability.yaml"
    assert state_file.exists()
    with open(state_file, 'r') as f:
        state_data = yaml.safe_load(f)
    assert state_data['regression_blocked'] is True
    
    # Check descriptive stats file
    stats_file = results_dir / "descriptive_stats.json"
    assert stats_file.exists()
    with open(stats_file, 'r') as f:
        stats_data = json.load(f)
    
    # Verify required fields
    assert 'file_count' in stats_data
    assert 'metrics' in stats_data
    assert 'note' in stats_data
    
    # If metrics exist, check for mean, median, std_dev
    if stats_data['metrics']:
        for metric_name, metric_data in stats_data['metrics'].items():
            assert 'mean' in metric_data
            assert 'median' in metric_data
            assert 'std_dev' in metric_data

def test_load_real_data_with_sufficient_files(temp_dirs):
    """
    Test load_real_data when file count >= 10.
    It should:
    1. Set regression_blocked: False in state/data_availability.yaml
    2. NOT generate descriptive_stats.json
    """
    config, raw_dir, state_dir, results_dir = temp_dirs
    
    # Create 10 dummy files
    for i in range(10):
        (raw_dir / f"dummy_{i}.edges.gz").touch()
    
    with patch('src.loader.fetch_snap_dataset', return_value=None):
        result = load_real_data(config)
    
    # Check return value
    assert result['file_count'] == 10
    assert result['regression_blocked'] is False
    
    # Check state file
    state_file = state_dir / "data_availability.yaml"
    assert state_file.exists()
    with open(state_file, 'r') as f:
        state_data = yaml.safe_load(f)
    assert state_data['regression_blocked'] is False
    
    # Check that descriptive stats file does NOT exist
    stats_file = results_dir / "descriptive_stats.json"
    assert not stats_file.exists()

def test_load_real_data_no_synthetic_fallback(temp_dirs):
    """
    Test that load_real_data does NOT generate synthetic graphs.
    It should strictly rely on real data fetches.
    """
    config, raw_dir, state_dir, results_dir = temp_dirs
    
    # Simulate fetches that fail (return None)
    with patch('src.loader.fetch_snap_dataset', return_value=None):
        result = load_real_data(config)
    
    # Verify that no synthetic files were created
    # The only files should be the dummy ones we created (if any) or none
    # We didn't create any dummy files in this test, so raw_dir should be empty
    # But the function might have created some? No, fetch_snap_dataset returns None, so no files are created.
    files_in_raw = list(raw_dir.iterdir())
    assert len(files_in_raw) == 0, "No files should be created if fetch fails and no synthetic fallback is used"
    
    # Verify regression_blocked is True because N=0 < 10
    assert result['regression_blocked'] is True
    
    # Verify descriptive_stats was generated
    stats_file = results_dir / "descriptive_stats.json"
    assert stats_file.exists()
    with open(stats_file, 'r') as f:
        stats_data = json.load(f)
    assert stats_data['file_count'] == 0
    assert 'note' in stats_data