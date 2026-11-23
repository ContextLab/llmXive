import pytest
import os
import tempfile
from pathlib import Path
from src.preprocessing.validate_exclusion_log import validate_exclusion_log

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary valid log file."""
    log_file = tmp_path / "covariate_exclusion_log.txt"
    log_file.write_text("Excluded 42 samples due to >20% missing covariate data.")
    return str(log_file)

@pytest.fixture
def temp_empty_log_file(tmp_path):
    """Create a temporary empty log file."""
    log_file = tmp_path / "covariate_exclusion_log.txt"
    log_file.write_text("")
    return str(log_file)

@pytest.fixture
def temp_invalid_log_file(tmp_path):
    """Create a temporary invalid log file (no count)."""
    log_file = tmp_path / "covariate_exclusion_log.txt"
    log_file.write_text("Some log content but no valid count format.")
    return str(log_file)

def test_validate_exclusion_log_success(temp_log_file):
    """Test successful validation of a valid log file."""
    result = validate_exclusion_log(temp_log_file)
    
    assert result['exists'] is True
    assert result['valid'] is True
    assert result['error'] is None
    assert 'excluded_samples' in result['counts']
    assert result['counts']['excluded_samples'] == 42

def test_validate_exclusion_log_file_not_found(tmp_path):
    """Test validation fails when file does not exist."""
    non_existent_path = str(tmp_path / "non_existent_file.txt")
    result = validate_exclusion_log(non_existent_path)
    
    assert result['exists'] is False
    assert result['valid'] is False
    assert result['error'] is not None
    assert "not found" in result['error'].lower()

def test_validate_exclusion_log_empty_file(temp_empty_log_file):
    """Test validation fails when file is empty."""
    result = validate_exclusion_log(temp_empty_log_file)
    
    assert result['exists'] is True
    assert result['valid'] is False
    assert result['error'] is not None
    assert "empty" in result['error'].lower()

def test_validate_exclusion_log_invalid_format(temp_invalid_log_file):
    """Test validation fails when file content is invalid."""
    result = validate_exclusion_log(temp_invalid_log_file)
    
    assert result['exists'] is True
    assert result['valid'] is False
    assert result['error'] is not None
    assert "parse" in result['error'].lower()
