"""
Unit tests for validate_pairing module.
Tests FR-009 and SC-005: Abort with E-PAIRING if pairing rate < 95%.
"""
import json
import pytest
from pathlib import Path
import tempfile
import os

# Import the module under test
from code.exceptions import E_PAIRING
from code.validate_pairing import (
    load_pairing_statistics,
    validate_pairing_rate,
    log_validation_results,
    run_pairing_validation
)

@pytest.fixture
def temp_pairing_log():
    """Create a temporary pairing log file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            'total_samples': 100,
            'paired_samples': 95,
            'unpaired_samples': 5,
            'pairing_rate': 0.95
        }
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_pairing_log_low_rate():
    """Create a temporary pairing log with low pairing rate."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            'total_samples': 100,
            'paired_samples': 80,
            'unpaired_samples': 20,
            'pairing_rate': 0.80
        }
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_pairing_log_empty():
    """Create a temporary pairing log with zero samples."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            'total_samples': 0,
            'paired_samples': 0,
            'unpaired_samples': 0,
            'pairing_rate': 0.0
        }
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_pairing_statistics(temp_pairing_log):
    """Test loading pairing statistics from a valid file."""
    stats = load_pairing_statistics(temp_pairing_log)
    assert stats['total_samples'] == 100
    assert stats['paired_samples'] == 95
    assert stats['unpaired_samples'] == 5

def test_load_pairing_statistics_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_pairing_statistics('nonexistent/path.json')

def test_validate_pairing_rate_pass():
    """Test validation passes when rate >= threshold."""
    stats = {'total_samples': 100, 'paired_samples': 95}
    is_valid, rate, message = validate_pairing_rate(stats, threshold=0.95)
    assert is_valid is True
    assert rate == 0.95
    assert 'PASSED' in message

def test_validate_pairing_rate_fail():
    """Test validation fails when rate < threshold."""
    stats = {'total_samples': 100, 'paired_samples': 80}
    is_valid, rate, message = validate_pairing_rate(stats, threshold=0.95)
    assert is_valid is False
    assert rate == 0.80
    assert 'FAILED' in message

def test_validate_pairing_rate_zero_samples():
    """Test that ValueError is raised for zero total samples."""
    stats = {'total_samples': 0, 'paired_samples': 0}
    with pytest.raises(ValueError):
        validate_pairing_rate(stats)

def test_log_validation_results():
    """Test logging validation results to a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / 'validation_results.json'
        log_validation_results(0.95, True, "Test message", str(log_path))
        
        assert log_path.exists()
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert data['pairing_rate'] == 0.95
        assert data['is_valid'] is True
        assert data['message'] == "Test message"

def test_run_pairing_validation_pass(temp_pairing_log):
    """Test that validation passes when rate meets threshold."""
    result = run_pairing_validation(temp_pairing_log, threshold=0.95)
    assert result is True

def test_run_pairing_validation_fail(temp_pairing_log_low_rate):
    """Test that E_PAIRING is raised when rate is below threshold."""
    with pytest.raises(E_PAIRING):
        run_pairing_validation(temp_pairing_log_low_rate, threshold=0.95)

def test_run_pairing_validation_zero_samples(temp_pairing_log_empty):
    """Test that ValueError is raised for zero samples."""
    with pytest.raises(ValueError):
        run_pairing_validation(temp_pairing_log_empty)

def test_pairing_rate_calculation_edge_cases():
    """Test edge cases for pairing rate calculation."""
    # 100% pairing
    stats = {'total_samples': 100, 'paired_samples': 100}
    is_valid, rate, _ = validate_pairing_rate(stats, threshold=0.95)
    assert is_valid is True
    assert rate == 1.0

    # 0% pairing
    stats = {'total_samples': 100, 'paired_samples': 0}
    is_valid, rate, _ = validate_pairing_rate(stats, threshold=0.95)
    assert is_valid is False
    assert rate == 0.0

    # Exact threshold
    stats = {'total_samples': 20, 'paired_samples': 19}
    is_valid, rate, _ = validate_pairing_rate(stats, threshold=0.95)
    assert is_valid is True
    assert rate == 0.95

def test_custom_threshold():
    """Test validation with custom threshold."""
    stats = {'total_samples': 100, 'paired_samples': 90}
    
    # Should pass with 0.85 threshold
    is_valid, rate, _ = validate_pairing_rate(stats, threshold=0.85)
    assert is_valid is True
    
    # Should fail with 0.95 threshold
    is_valid, rate, _ = validate_pairing_rate(stats, threshold=0.95)
    assert is_valid is False