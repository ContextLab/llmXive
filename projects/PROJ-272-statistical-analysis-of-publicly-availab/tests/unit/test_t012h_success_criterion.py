"""
Unit tests for T012h: Success Criterion SC-001.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# We need to mock the config.get_path to point to temp directories during tests
import sys
from unittest.mock import patch, MagicMock

# Import the functions to test
from t012h_success_criterion import (
    load_raw_record_count,
    load_cleaned_record_count,
    calculate_valid_label_proportion,
    save_metadata,
    main
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir) / "results"
        interim_dir = Path(tmpdir) / "interim"
        results_dir.mkdir()
        interim_dir.mkdir()
        yield {
            "results": results_dir,
            "interim": interim_dir,
            "tmp": Path(tmpdir)
        }

@patch('t012h_success_criterion.get_path')
def test_load_raw_record_count_success(mock_get_path, temp_dirs):
    """Test loading valid raw record count."""
    mock_path = temp_dirs["results"] / "raw_record_count.json"
    mock_get_path.return_value = mock_path
    
    # Create mock file
    with open(mock_path, 'w') as f:
        json.dump({"raw_count": 100}, f)
    
    count = load_raw_record_count()
    assert count == 100

@patch('t012h_success_criterion.get_path')
def test_load_raw_record_count_missing_file(mock_get_path, temp_dirs):
    """Test error handling for missing raw count file."""
    mock_path = temp_dirs["results"] / "raw_record_count.json"
    mock_get_path.return_value = mock_path
    
    with pytest.raises(FileNotFoundError):
        load_raw_record_count()

@patch('t012h_success_criterion.get_path')
def test_load_raw_record_count_invalid_schema(mock_get_path, temp_dirs):
    """Test error handling for invalid schema in raw count file."""
    mock_path = temp_dirs["results"] / "raw_record_count.json"
    mock_get_path.return_value = mock_path
    
    with open(mock_path, 'w') as f:
        json.dump({"other_key": 100}, f)
    
    with pytest.raises(ValueError):
        load_raw_record_count()

@patch('t012h_success_criterion.get_path')
def test_load_cleaned_record_count_success(mock_get_path, temp_dirs):
    """Test loading valid cleaned record count."""
    mock_path = temp_dirs["interim"] / "cleaned_adress.csv"
    mock_get_path.return_value = mock_path
    
    # Create mock CSV
    df = pd.DataFrame({"text": ["a" * 100] * 50, "label": ["Control"] * 50})
    df.to_csv(mock_path, index=False)
    
    count = load_cleaned_record_count()
    assert count == 50

@patch('t012h_success_criterion.get_path')
def test_load_cleaned_record_count_missing_file(mock_get_path, temp_dirs):
    """Test error handling for missing cleaned dataset file."""
    mock_path = temp_dirs["interim"] / "cleaned_adress.csv"
    mock_get_path.return_value = mock_path
    
    with pytest.raises(FileNotFoundError):
        load_cleaned_record_count()

def test_calculate_valid_label_proportion():
    """Test proportion calculation."""
    # Standard case
    prop = calculate_valid_label_proportion(100, 80)
    assert prop == 0.8
    
    # Edge case: all valid
    prop = calculate_valid_label_proportion(100, 100)
    assert prop == 1.0
    
    # Edge case: none valid
    prop = calculate_valid_label_proportion(100, 0)
    assert prop == 0.0

def test_calculate_valid_label_proportion_zero_division():
    """Test zero division error."""
    with pytest.raises(ZeroDivisionError):
        calculate_valid_label_proportion(0, 0)

@patch('t012h_success_criterion.get_path')
def test_save_metadata(mock_get_path, temp_dirs):
    """Test saving metadata to file."""
    mock_path = temp_dirs["results"] / "metadata_partial_h.json"
    mock_get_path.return_value = mock_path
    
    result_path = save_metadata(0.75)
    
    assert result_path == mock_path
    assert mock_path.exists()
    
    with open(mock_path, 'r') as f:
        data = json.load(f)
    
    assert "valid_label_proportion" in data
    assert data["valid_label_proportion"] == 0.75