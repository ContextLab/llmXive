"""
Tests for Final Validation Module (T035)

These tests verify that the validation logic correctly identifies
missing, empty, or invalid artifacts.
"""
import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock config for testing
class MockConfig:
    DATA_PROCESSED_DIR = "tests/tmp_data"
    LOGS_DIR = "tests/tmp_logs"

# Patch the config import in the module under test
import sys
from unittest.mock import MagicMock

# Create temporary directories
TEST_DATA_DIR = Path("tests/tmp_data")
TEST_LOGS_DIR = Path("tests/tmp_logs")

def setup_module(module):
    """Create temporary directories for tests."""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def teardown_module(module):
    """Clean up temporary directories."""
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
    if TEST_LOGS_DIR.exists():
        shutil.rmtree(TEST_LOGS_DIR)

# We need to mock the config module before importing final_validation
# Since final_validation imports from code.config, we need to ensure
# our mock paths are used.

# Instead of mocking, we will test the logic by creating files in the
# expected locations and then calling the functions directly.
# We will temporarily override the constants in the module.

import code.final_validation as fv

def test_check_file_exists_found():
    """Test that check_file_exists returns True for existing non-empty file."""
    test_file = TEST_DATA_DIR / "test_file.txt"
    test_file.write_text("Some content")
    
    assert fv.check_file_exists(test_file) is True
    test_file.unlink()

def test_check_file_exists_missing():
    """Test that check_file_exists returns False for missing file."""
    test_file = TEST_DATA_DIR / "nonexistent.txt"
    
    assert fv.check_file_exists(test_file) is False

def test_check_file_exists_empty():
    """Test that check_file_exists returns False for empty file."""
    test_file = TEST_DATA_DIR / "empty.txt"
    test_file.write_text("")
    
    assert fv.check_file_exists(test_file) is False
    test_file.unlink()

def test_check_csv_content_valid():
    """Test that check_csv_content returns True for valid CSV."""
    test_file = TEST_DATA_DIR / "valid.csv"
    with open(test_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['col1', 'col2'])
        writer.writeheader()
        writer.writerow({'col1': 'a', 'col2': 'b'})
    
    assert fv.check_csv_content(test_file, required_columns=['col1', 'col2']) is True
    test_file.unlink()

def test_check_csv_content_missing_columns():
    """Test that check_csv_content returns False for missing columns."""
    test_file = TEST_DATA_DIR / "bad_cols.csv"
    with open(test_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['col1'])
        writer.writeheader()
        writer.writerow({'col1': 'a'})
    
    assert fv.check_csv_content(test_file, required_columns=['col1', 'col2']) is False
    test_file.unlink()

def test_check_csv_content_empty():
    """Test that check_csv_content returns False for empty CSV."""
    test_file = TEST_DATA_DIR / "empty.csv"
    test_file.write_text("")
    
    assert fv.check_csv_content(test_file) is False
    test_file.unlink()

def test_check_log_content_valid():
    """Test that check_log_content returns True for valid log."""
    test_file = TEST_LOGS_DIR / "valid.log"
    test_file.write_text("INFO: Success\nERROR: None\n")
    
    assert fv.check_log_content(test_file, required_keywords=['Success']) is True
    test_file.unlink()

def test_check_log_content_missing_keyword():
    """Test that check_log_content returns False for missing keyword."""
    test_file = TEST_LOGS_DIR / "bad_log.log"
    test_file.write_text("INFO: Failed\n")
    
    assert fv.check_log_content(test_file, required_keywords=['Success']) is False
    test_file.unlink()

def test_check_log_content_empty():
    """Test that check_log_content returns False for empty log."""
    test_file = TEST_LOGS_DIR / "empty.log"
    test_file.write_text("")
    
    assert fv.check_log_content(test_file) is False
    test_file.unlink()

def test_main_success_scenario(monkeypatch):
    """
    Test main() returns 0 when all required files exist and are valid.
    """
    # Create all required files
    required_files = [
        "energy_results_aggregated.csv",
        "stats_report.csv",
        "energy_bar.png",
        "tradeoff_scatter.png"
    ]
    
    required_logs = [
        "pipeline_duration.log"
    ]

    # Create CSV files with valid content
    csv_data = "model_id,problem_id,tokens_generated,energy_kwh,runtime_seconds,pass_fail_status\nmodel1,1,10,0.5,1.0,1\n"
    for f in required_files:
        if f.endswith('.csv'):
            file_path = TEST_DATA_DIR / f
            file_path.write_text(csv_data)
        elif f.endswith('.png'):
            # Create a dummy PNG file (minimal valid PNG header)
            file_path = TEST_DATA_DIR / f
            file_path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'x' * 100)
    
    # Create log file
    for f in required_logs:
        file_path = TEST_LOGS_DIR / f
        file_path.write_text("Pipeline completed successfully.\n")

    # Temporarily override the constants in the module
    original_data_dir = fv.DATA_PROCESSED_DIR
    original_logs_dir = fv.LOGS_DIR
    
    fv.DATA_PROCESSED_DIR = str(TEST_DATA_DIR)
    fv.LOGS_DIR = str(TEST_LOGS_DIR)

    try:
        result = fv.main()
        assert result == 0
    finally:
        # Restore original constants
        fv.DATA_PROCESSED_DIR = original_data_dir
        fv.LOGS_DIR = original_logs_dir

    # Cleanup
    for f in required_files + required_logs:
        path = TEST_DATA_DIR / f if not f.endswith('.log') else TEST_LOGS_DIR / f
        if path.exists():
            path.unlink()

def test_main_missing_file_scenario(monkeypatch):
    """
    Test main() returns 1 when a required file is missing.
    """
    # Create only some required files
    partial_files = [
        "stats_report.csv",
        "energy_bar.png",
        "tradeoff_scatter.png"
    ]
    
    # Create CSV file
    csv_data = "model_id,problem_id,tokens_generated,energy_kwh,runtime_seconds,pass_fail_status\nmodel1,1,10,0.5,1.0,1\n"
    for f in partial_files:
        if f.endswith('.csv'):
            file_path = TEST_DATA_DIR / f
            file_path.write_text(csv_data)
        elif f.endswith('.png'):
            file_path = TEST_DATA_DIR / f
            file_path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'x' * 100)
    
    # Create log file
    log_path = TEST_LOGS_DIR / "pipeline_duration.log"
    log_path.write_text("Pipeline completed successfully.\n")

    # Temporarily override the constants in the module
    original_data_dir = fv.DATA_PROCESSED_DIR
    original_logs_dir = fv.LOGS_DIR
    
    fv.DATA_PROCESSED_DIR = str(TEST_DATA_DIR)
    fv.LOGS_DIR = str(TEST_LOGS_DIR)

    try:
        result = fv.main()
        assert result == 1
    finally:
        # Restore original constants
        fv.DATA_PROCESSED_DIR = original_data_dir
        fv.LOGS_DIR = original_logs_dir

    # Cleanup
    for f in partial_files:
        path = TEST_DATA_DIR / f
        if path.exists():
            path.unlink()
    if log_path.exists():
        log_path.unlink()
