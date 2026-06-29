"""
Unit tests for logging utilities.

These tests verify that the exclusion logging infrastructure works correctly
and maintains proper CSV formatting.
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest

# We'll test by temporarily redirecting the log path
from utils.logging_utils import (
    init_exclusion_log,
    log_exclusion,
    read_exclusion_log,
    get_exclusion_count,
    clear_exclusion_log,
    CSV_HEADER,
    EXCLUSION_LOG_PATH
)

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override the log path
        original_path = EXCLUSION_LOG_PATH
        temp_path = Path(tmpdir) / "exclusion.log"
        
        # We can't easily override the module-level constant, so we'll
        # test by creating the logs directory and using the actual path
        os.makedirs("logs", exist_ok=True)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

def test_init_exclusion_log_creates_file():
    """Test that init_exclusion_log creates the log file with header."""
    # Clear any existing log
    if EXCLUSION_LOG_PATH.exists():
        EXCLUSION_LOG_PATH.unlink()
    
    # Initialize
    init_exclusion_log()
    
    # Verify file exists
    assert EXCLUSION_LOG_PATH.exists()
    
    # Verify header is correct
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == CSV_HEADER

def test_init_exclusion_log_idempotent():
    """Test that calling init multiple times doesn't duplicate header."""
    # Initialize twice
    init_exclusion_log()
    init_exclusion_log()
    
    # Count lines (should be exactly 1 - the header)
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1

def test_log_exclusion_appends_entry():
    """Test that log_exclusion appends a new entry to the log."""
    # Clear log first
    clear_exclusion_log()
    
    initial_count = get_exclusion_count()
    
    # Log an exclusion
    log_exclusion(
        dataset_id="test_dataset",
        missing_variable_name="age",
        reason="Test exclusion reason"
    )
    
    # Verify count increased
    assert get_exclusion_count() == initial_count + 1

def test_log_exclusion_csv_format():
    """Test that logged entries have correct CSV format."""
    # Clear and log
    clear_exclusion_log()
    log_exclusion(
        dataset_id="adult",
        missing_variable_name="income",
        reason="Income column missing"
    )
    
    # Read and verify
    entries = read_exclusion_log()
    assert len(entries) == 1
    
    entry = entries[0]
    assert entry['dataset_id'] == 'adult'
    assert entry['missing_variable_name'] == 'income'
    assert entry['reason'] == 'Income column missing'
    assert 'timestamp' in entry
    assert len(entry['timestamp']) > 0

def test_read_exclusion_log_empty():
    """Test reading an empty log returns empty list."""
    clear_exclusion_log()
    entries = read_exclusion_log()
    assert entries == []

def test_clear_exclusion_log():
    """Test that clear_exclusion_log removes all entries."""
    # Add some entries
    clear_exclusion_log()
    log_exclusion("ds1", "var1", "reason1")
    log_exclusion("ds2", "var2", "reason2")
    
    assert get_exclusion_count() == 2
    
    # Clear
    clear_exclusion_log()
    
    assert get_exclusion_count() == 0
    
    # Verify header still exists
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        assert 'timestamp' in lines[0]

def test_csv_header_constant():
    """Test that CSV_HEADER constant has correct columns."""
    expected = ["timestamp", "dataset_id", "missing_variable_name", "reason"]
    assert CSV_HEADER == expected
    assert len(CSV_HEADER) == 4
