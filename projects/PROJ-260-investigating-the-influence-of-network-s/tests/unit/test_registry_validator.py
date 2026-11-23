import json
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.registry_validator import (
    validate_dataset_id,
    validate_registry,
    write_validation_log,
    write_valid_sources,
    setup_logger
)

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def sample_registry():
    return {
        "1000": ["valid_id_1"],
        "2000": ["valid_id_2", "invalid_id_1"],
        "4000": ["valid_id_3"]
    }

def test_validate_registry_valid_ids(sample_registry, temp_dir):
    """Test validation of a registry with all valid IDs."""
    mock_logger = MagicMock(spec=logging.Logger)
    
    # Mock validate_dataset_id to return True for all
    with patch('src.services.registry_validator.validate_dataset_id', return_value=True):
        results = validate_registry(sample_registry, mock_logger)
        
    assert results['all_valid'] is True
    assert len(results['valid_ids']) == 4
    assert len(results['invalid_ids']) == 0

def test_validate_registry_mixed_ids(sample_registry, temp_dir):
    """Test validation of a registry with mixed valid/invalid IDs."""
    mock_logger = MagicMock(spec=logging.Logger)
    
    # Mock validate_dataset_id to return False for invalid_id_1
    def mock_validator(dataset_id, logger):
        return dataset_id != "invalid_id_1"
    
    with patch('src.services.registry_validator.validate_dataset_id', side_effect=mock_validator):
        results = validate_registry(sample_registry, mock_logger)
        
    assert results['all_valid'] is False
    assert "invalid_id_1" in results['invalid_ids']
    assert len(results['valid_ids']) == 3

def test_write_validation_log(temp_dir):
    """Test writing the validation log."""
    results = {
        'valid_ids': ['id1', 'id2'],
        'invalid_ids': ['id3'],
        'all_valid': False
    }
    registry_path = temp_dir / "registry.json"
    log_path = temp_dir / "log.txt"
    
    write_validation_log(log_path, results, registry_path)
    
    assert log_path.exists()
    content = log_path.read_text()
    assert "Valid IDs" in content
    assert "Invalid IDs" in content
    assert "id1" in content
    assert "id3" in content

def test_write_valid_sources(temp_dir):
    """Test writing valid sources to JSON."""
    valid_ids = ["id1", "id2"]
    output_path = temp_dir / "valid_sources.json"
    
    write_valid_sources(valid_ids, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    assert data == valid_ids