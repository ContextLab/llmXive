import os
import sys
import pytest
from pathlib import Path

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import get_config, ensure_dirs

def test_get_config_returns_dict():
    """Test that get_config returns a dictionary."""
    config = get_config()
    assert isinstance(config, dict)
    assert 'data' in config
    assert 'output' in config
    assert 'datasets' in config
    assert 'dataset_openml_ids' in config
    assert 'random_seed' in config

def test_config_paths_exist_in_structure():
    """Test that config contains expected path keys."""
    config = get_config()
    assert 'raw' in config['data']
    assert 'processed' in config['data']
    assert 'results' in config['output']
    assert 'plots' in config['output']
    assert 'reports' in config['output']

def test_config_has_openml_ids():
    """Test that the config has OpenML IDs for datasets."""
    config = get_config()
    expected_datasets = ['wine', 'abalone', 'breast_cancer', 'student_performance', 'air_quality', 'concrete']
    for ds in expected_datasets:
        assert ds in config['dataset_openml_ids']
        assert isinstance(config['dataset_openml_ids'][ds], int)

def test_ensure_dirs_creates_directories(tmp_path):
    """Test that ensure_dirs creates the necessary directories."""
    # Create a temporary config pointing to tmp_path
    test_config = {
        'data': {'raw': str(tmp_path / 'data' / 'raw'), 'processed': str(tmp_path / 'data' / 'processed')},
        'output': {'results': str(tmp_path / 'output' / 'results'), 'plots': str(tmp_path / 'output' / 'plots')},
        'state': {'project_path': str(tmp_path / 'state' / 'test.yaml')}
    }
    ensure_dirs(test_config)
    
    assert (tmp_path / 'data' / 'raw').exists()
    assert (tmp_path / 'data' / 'processed').exists()
    assert (tmp_path / 'output' / 'results').exists()
    assert (tmp_path / 'output' / 'plots').exists()
    assert (tmp_path / 'state').exists()