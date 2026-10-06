import pytest
import os
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'code'))

from data.stream_recipe1m import (
    flatten_recipe,
    load_sample_size_requirement,
    load_amendment_log,
    ensure_directories,
    write_validation_log
)

@pytest.fixture
def mock_amendment_log(tmp_path):
    """Create a mock amendment log for testing."""
    amendment_file = tmp_path / 'amendment_log.json'
    amendment_data = {
        "status": "RATIFIED",
        "methodology": "Correlational Analysis",
        "proxy_source": "Recipe1M",
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(amendment_file, 'w') as f:
        json.dump(amendment_data, f)
    return amendment_file

@pytest.fixture
def mock_pilot_stats(tmp_path):
    """Create a mock pilot stats file."""
    pilot_file = tmp_path / 'pilot_stats.json'
    pilot_data = {
        "sample_size_required": 5000,
        "status": "SUCCESS"
    }
    with open(pilot_file, 'w') as f:
        json.dump(pilot_data, f)
    return pilot_file

def test_flatten_recipe_basic():
    """Test basic recipe flattening."""
    recipe = {
        'id': '123',
        'title': 'Test Recipe',
        'rating': 4.5,
        'ingredients': ['flour', 'sugar', 'eggs'],
        'instructions': ['mix', 'bake'],
        'url': 'http://example.com'
    }
    result = flatten_recipe(recipe)
    
    assert result['recipe_id'] == '123'
    assert result['title'] == 'Test Recipe'
    assert result['rating'] == 4.5
    assert 'flour' in result['ingredients_str']
    assert 'sugar' in result['ingredients_str']
    assert 'eggs' in result['ingredients_str']
    assert 'recipe_id' in result
    assert 'ingredients_str' in result

def test_flatten_recipe_empty():
    """Test flattening with minimal data."""
    recipe = {'id': '456'}
    result = flatten_recipe(recipe)
    
    assert result['recipe_id'] == '456'
    assert result['rating'] is None
    assert result['ingredients_str'] == ''
    assert result['title'] == ''

def test_load_sample_size_requirement_missing(mock_pilot_stats, tmp_path):
    """Test loading sample size when file exists."""
    # Temporarily change working directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Mock the project root path resolution
        with patch('data.stream_recipe1m.project_root', tmp_path):
            size = load_sample_size_requirement()
            assert size == 5000
    finally:
        os.chdir(original_cwd)

def test_load_sample_size_requirement_default(tmp_path):
    """Test default sample size when file missing."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        with patch('data.stream_recipe1m.project_root', tmp_path):
            size = load_sample_size_requirement()
            assert size == 10000  # Default fallback
    finally:
        os.chdir(original_cwd)

def test_load_amendment_log_valid(mock_amendment_log, tmp_path):
    """Test loading valid amendment log."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        with patch('data.stream_recipe1m.project_root', tmp_path):
            amendment = load_amendment_log()
            assert amendment['status'] == 'RATIFIED'
            assert amendment['methodology'] == 'Correlational Analysis'
    finally:
        os.chdir(original_cwd)

def test_write_validation_log(tmp_path):
    """Test writing validation log."""
    logs_dir = tmp_path / 'logs'
    logs_dir.mkdir()
    
    with patch('data.stream_recipe1m.project_root', tmp_path):
        write_validation_log(True, logs_dir)
    
    validation_file = logs_dir / 'recipe1m_validation.json'
    assert validation_file.exists()
    
    with open(validation_file, 'r') as f:
        data = json.load(f)
    
    assert data['rating_column_present'] is True
    assert data['status'] == 'VALIDATED'
    assert 'timestamp' in data
    assert data['task_id'] == 'T013a'

def test_ensure_directories(tmp_path):
    """Test directory creation."""
    with patch('data.stream_recipe1m.project_root', tmp_path):
        raw, logs = ensure_directories()
        
    assert (tmp_path / 'data' / 'raw').exists()
    assert (tmp_path / 'data' / 'logs').exists()
    assert raw == tmp_path / 'data' / 'raw'
    assert logs == tmp_path / 'data' / 'logs'
