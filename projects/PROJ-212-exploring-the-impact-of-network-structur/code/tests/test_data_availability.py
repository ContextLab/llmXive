import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

from src.data_availability import check_data_availability, main

@pytest.fixture
def temp_project_dirs():
    """Create temporary directories mimicking the project structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_raw = tmp_path / 'data' / 'raw'
        state = tmp_path / 'state'
        data_raw.mkdir(parents=True)
        state.mkdir(parents=True)
        
        config_content = {
            'paths': {
                'data_raw': str(data_raw),
                'state': str(state)
            },
            'thresholds': {
                'data_count': 10
            }
        }
        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        yield {
            'base': tmp_path,
            'data_raw': data_raw,
            'state': state,
            'config': config_file
        }

def test_insufficient_data_generates_stats(temp_project_dirs):
    """Test that regression_blocked is true when file count < 10."""
    data_raw = temp_project_dirs['data_raw']
    
    # Create 5 files
    for i in range(5):
        (data_raw / f'file_{i}.mtx').touch()
        
    result = check_data_availability(data_raw, threshold=10)
    
    assert result['regression_blocked'] is True
    assert result['file_count'] == 5
    assert 'Insufficient data' in result['reason']

def test_sufficient_data_no_stats(temp_project_dirs):
    """Test that regression_blocked is false when file count >= 10."""
    data_raw = temp_project_dirs['data_raw']
    
    # Create 15 files
    for i in range(15):
        (data_raw / f'file_{i}.mtx').touch()
        
    result = check_data_availability(data_raw, threshold=10)
    
    assert result['regression_blocked'] is False
    assert result['file_count'] == 15
    assert result['reason'] is None

def test_empty_raw_directory(temp_project_dirs):
    """Test behavior when raw directory is empty."""
    data_raw = temp_project_dirs['data_raw']
    
    result = check_data_availability(data_raw, threshold=10)
    
    assert result['regression_blocked'] is True
    assert result['file_count'] == 0

def test_missing_raw_directory(temp_project_dirs):
    """Test behavior when raw directory does not exist."""
    non_existent = temp_project_dirs['data_raw'].parent / 'non_existent'
    
    result = check_data_availability(non_existent, threshold=10)
    
    assert result['regression_blocked'] is True
    assert result['file_count'] == 0
    assert 'missing' in result['reason']

def test_main_writes_yaml_file(temp_project_dirs):
    """Test that main() writes the correct YAML file."""
    data_raw = temp_project_dirs['data_raw']
    state_dir = temp_project_dirs['state']
    config_file = temp_project_dirs['config']
    
    # Create 3 files
    for i in range(3):
        (data_raw / f'file_{i}.mtx').touch()
        
    with patch('config.load_config') as mock_load_config, \
         patch('config.get_paths') as mock_get_paths:
         
        mock_load_config.return_value = {}
        mock_get_paths.return_value = {
            'data_raw': data_raw,
            'state': state_dir
        }
        
        main()
        
        output_file = state_dir / 'data_availability.yaml'
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            content = yaml.safe_load(f)
            
        assert content['regression_blocked'] is True
        assert content['file_count'] == 3
