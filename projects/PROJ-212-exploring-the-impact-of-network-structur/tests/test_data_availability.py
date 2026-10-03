"""
Tests for data availability checking logic.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

from src.data_availability import check_data_availability, write_state_file, main

@pytest.fixture
def temp_project_dirs():
    """Create temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_raw = tmp_path / 'data' / 'raw'
        state_dir = tmp_path / 'state'
        logs_dir = tmp_path / 'logs'
        
        data_raw.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)
        
        yield {
            'root': tmp_path,
            'raw': data_raw,
            'state': state_dir,
            'logs': logs_dir
        }

def test_insufficient_data_generates_state(temp_project_dirs):
    """Test that insufficient data sets regression_blocked to true."""
    raw_dir = temp_project_dirs['raw']
    state_dir = temp_project_dirs['state']
    
    # Create 5 files (less than threshold of 10)
    for i in range(5):
        (raw_dir / f'file_{i}.txt').touch()
        
    state = check_data_availability(raw_dir, threshold=10)
    
    assert state['file_count'] == 5
    assert state['regression_blocked'] is True

def test_sufficient_data_no_block(temp_project_dirs):
    """Test that sufficient data sets regression_blocked to false."""
    raw_dir = temp_project_dirs['raw']
    state_dir = temp_project_dirs['state']
    
    # Create 15 files (more than threshold of 10)
    for i in range(15):
        (raw_dir / f'file_{i}.txt').touch()
        
    state = check_data_availability(raw_dir, threshold=10)
    
    assert state['file_count'] == 15
    assert state['regression_blocked'] is False

def test_empty_raw_directory(temp_project_dirs):
    """Test that empty raw directory sets regression_blocked to true."""
    raw_dir = temp_project_dirs['raw']
    # Directory exists but is empty
    
    state = check_data_availability(raw_dir, threshold=10)
    
    assert state['file_count'] == 0
    assert state['regression_blocked'] is True

def test_missing_raw_directory(temp_project_dirs):
    """Test that missing raw directory sets regression_blocked to true."""
    raw_dir = temp_project_dirs['raw'] / 'nonexistent'
    state_dir = temp_project_dirs['state']
    
    state = check_data_availability(raw_dir, threshold=10)
    
    assert state['file_count'] == 0
    assert state['regression_blocked'] is True

def test_write_state_file(temp_project_dirs):
    """Test that state is correctly written to YAML file."""
    raw_dir = temp_project_dirs['raw']
    state_dir = temp_project_dirs['state']
    output_file = state_dir / 'data_availability.yaml'
    
    # Create 3 files
    for i in range(3):
        (raw_dir / f'file_{i}.txt').touch()
        
    state = check_data_availability(raw_dir, threshold=10)
    write_state_file(state, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded_state = yaml.safe_load(f)
        
    assert loaded_state['file_count'] == 3
    assert loaded_state['regression_blocked'] is True

def test_main_writes_yaml_file(temp_project_dirs, tmp_path):
    """Test that main() function writes the state file correctly."""
    # Mock config and paths
    mock_config = {
        'thresholds': {'min_files': 10},
        'paths': {
            'raw_data': str(temp_project_dirs['raw']),
            'state': str(temp_project_dirs['state'])
        }
    }
    
    output_file = temp_project_dirs['state'] / 'data_availability.yaml'
    
    # Create some files
    for i in range(5):
        (temp_project_dirs['raw'] / f'file_{i}.txt').touch()
        
    with patch('src.data_availability.load_config', return_value=mock_config):
        with patch('src.data_availability.get_paths', return_value=mock_config['paths']):
            main()
            
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded_state = yaml.safe_load(f)
        
    assert loaded_state['file_count'] == 5
    assert loaded_state['regression_blocked'] is True
