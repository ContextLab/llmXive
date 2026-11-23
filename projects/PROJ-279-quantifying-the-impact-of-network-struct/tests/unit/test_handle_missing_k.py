"""
Unit tests for the handle_missing_k module (Task T026).
Tests the logic for identifying and handling missing thermal conductivity values.
"""
import pytest
import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the config and logging modules before importing the target module
import sys
from types import ModuleType

# Create mock modules
mock_env_config = ModuleType('config.env_config')
mock_env_config.get_processed_dir = lambda: Path('/tmp/test_processed')
sys.modules['config.env_config'] = mock_env_config

mock_logging_config = ModuleType('logging_config')
mock_logger = MagicMock()
mock_logging_config.get_logger = lambda name: mock_logger
sys.modules['logging_config'] = mock_logging_config

from handle_missing_k import (
    load_processed_configs,
    identify_missing_k,
    handle_missing_k_values,
    save_missing_k_report
)

@pytest.fixture
def sample_configs():
    """Sample configurations for testing."""
    return [
        {"config_id": "cfg_001", "k": 1.5, "ring_dist": 5, "q6": 0.2},
        {"config_id": "cfg_002", "k": None, "ring_dist": 6, "q6": 0.3},
        {"config_id": "cfg_003", "k": "", "ring_dist": 4, "q6": 0.1},
        {"config_id": "cfg_004", "k": "NaN", "ring_dist": 7, "q6": 0.4},
        {"config_id": "cfg_005", "k": 2.0, "ring_dist": 5, "q6": 0.25},
        {"config_id": "cfg_006", "thermal_conductivity": 1.8, "ring_dist": 6, "q6": 0.35},
        {"config_id": "cfg_007", "thermal_conductivity": None, "ring_dist": 5, "q6": 0.2},
        {"config_id": "cfg_008", "ring_dist": 5, "q6": 0.2}, # No k field at all
    ]

@pytest.fixture
def temp_descriptors_file(sample_configs, tmp_path):
    """Create a temporary CSV file with sample descriptors."""
    # Create the directory if it doesn't exist
    tmp_path.mkdir(parents=True, exist_ok=True)
    
    file_path = tmp_path / "descriptors.csv"
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sample_configs[0].keys())
        writer.writeheader()
        writer.writerows(sample_configs)
    
    return file_path

def test_identify_missing_k(sample_configs):
    """Test the identify_missing_k function."""
    valid, missing = identify_missing_k(sample_configs)
    
    # Valid configs: cfg_001, cfg_005, cfg_006
    assert len(valid) == 3
    valid_ids = [c['config_id'] for c in valid]
    assert 'cfg_001' in valid_ids
    assert 'cfg_005' in valid_ids
    assert 'cfg_006' in valid_ids
    
    # Missing configs: cfg_002, cfg_003, cfg_004, cfg_007, cfg_008
    assert len(missing) == 5
    missing_ids = [c['config_id'] for c in missing]
    assert 'cfg_002' in missing_ids
    assert 'cfg_003' in missing_ids
    assert 'cfg_004' in missing_ids
    assert 'cfg_007' in missing_ids
    assert 'cfg_008' in missing_ids

def test_handle_missing_k_values(sample_configs):
    """Test the handle_missing_k_values function."""
    valid, skip_count = handle_missing_k_values(sample_configs)
    
    assert skip_count == 5
    assert len(valid) == 3
    
    # Verify logger was called for skipping
    assert mock_logger.warning.called
    assert "Skipping 5 configuration(s)" in mock_logger.warning.call_args[0][0]

def test_save_missing_k_report(tmp_path):
    """Test saving the missing k report."""
    missing_configs = [
        {"config_id": "cfg_002", "k": None},
        {"config_id": "cfg_003", "k": ""},
    ]
    skip_count = 2
    
    report_path = save_missing_k_report(missing_configs, skip_count)
    
    assert report_path.exists()
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    assert report_data['skip_count'] == 2
    assert len(report_data['skipped_configs']) == 2
    assert report_data['skipped_configs'][0]['config_id'] == 'cfg_002'
    assert report_data['skipped_configs'][0]['reason'] == "Missing thermal conductivity value"

def test_load_processed_configs(temp_descriptors_file):
    """Test loading processed configs from CSV."""
    # Patch the get_processed_dir to return the temp directory
    with patch('handle_missing_k.get_processed_dir', return_value=temp_descriptors_file.parent):
        configs = load_processed_configs()
        
        assert len(configs) == 8
        assert configs[0]['config_id'] == 'cfg_001'
        assert configs[0]['k'] == '1.5' # CSV reads as string

def test_handle_missing_k_with_no_missing(sample_configs):
    """Test handling when no configs are missing k."""
    # Modify sample to have no missing k
    clean_configs = [
        {"config_id": f"cfg_{i:03d}", "k": 1.5 + i * 0.1, "ring_dist": 5, "q6": 0.2}
        for i in range(5)
    ]
    
    valid, skip_count = handle_missing_k_values(clean_configs)
    
    assert skip_count == 0
    assert len(valid) == 5
    
    # Verify info log was called
    assert any("No configurations with missing thermal conductivity values found" in str(call) 
               for call in mock_logger.info.call_args_list)