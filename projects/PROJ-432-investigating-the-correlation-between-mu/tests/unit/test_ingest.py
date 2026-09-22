"""
Unit tests for ingestion logic (alignment, logging).
"""
import pytest
from pathlib import Path
import sys
import os
import tempfile
import shutil
import json
import pandas as pd

from src.data.ingest import log_exclusion_event, align_temporal_data

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

def test_log_exclusion_event_creates_file(temp_data_dir):
    """Test that log_exclusion_event creates the log file if it doesn't exist."""
    log_file = temp_data_dir / "alignment.json"
    
    # Mock the LOGS_DIR usage by temporarily patching or passing a custom path
    # Since the function uses a global LOGS_DIR, we need to test the file creation logic
    # by directly calling it and checking the file.
    # For this test, we assume the function writes to the global LOGS_DIR.
    # To make it testable, we might need to refactor, but for now we test the file content.
    
    # We will create a temporary log file path by patching the global variable
    # or by assuming the test environment sets LOGS_DIR to temp_data_dir.
    # Let's assume the global LOGS_DIR is set to temp_data_dir for this test.
    # In a real test, we would mock the function or the module.
    
    # Simpler approach: Just call the function and check if the file exists in the expected global location.
    # But since we can't easily change the global LOGS_DIR in the module, we will test the logic
    # by creating a mock file and checking the append logic.
    
    # For this specific test, we will assume the test runner sets the environment or we test the file directly.
    # Let's just test the file creation and content.
    
    # We will create a temporary file to simulate the log
    test_log = temp_data_dir / "alignment.json"
    
    # Since we can't easily change the global variable in the module, we will test the function
    # by assuming it writes to the global LOGS_DIR.
    # We will instead test the logic by creating a mock file and checking the content.
    # This is a limitation of the current design.
    # We will assume the test environment is set up correctly.
    
    # Let's just test the file creation by calling the function and checking the file.
    # We will assume the global LOGS_DIR is set to temp_data_dir for this test.
    # This is a bit hacky, but it works for unit testing.
    
    # We will patch the LOGS_DIR in the module
    import src.data.ingest as ingest_module
    original_logs_dir = ingest_module.LOGS_DIR
    ingest_module.LOGS_DIR = temp_data_dir
    
    try:
        log_exclusion_event("2023-01-01", "missing_era5", "era5")
        assert test_log.exists()
        
        with open(test_log, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['date'] == "2023-01-01"
        assert data[0]['reason'] == "missing_era5"
    finally:
        ingest_module.LOGS_DIR = original_logs_dir

def test_log_exclusion_event_appends_to_existing(temp_data_dir):
    """Test that log_exclusion_event appends to an existing log file."""
    import src.data.ingest as ingest_module
    original_logs_dir = ingest_module.LOGS_DIR
    ingest_module.LOGS_DIR = temp_data_dir
    
    test_log = temp_data_dir / "alignment.json"
    
    # Create initial log
    with open(test_log, 'w') as f:
        json.dump([{"date": "2023-01-01", "reason": "test", "source": "test"}], f)
    
    try:
        log_exclusion_event("2023-01-02", "missing_icecube", "icecube")
        
        with open(test_log, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[1]['date'] == "2023-01-02"
    finally:
        ingest_module.LOGS_DIR = original_logs_dir

def test_align_temporal_data_logs_missing_dates(temp_data_dir):
    """Test that align_temporal_data logs exclusion events for missing dates."""
    import src.data.ingest as ingest_module
    original_logs_dir = ingest_module.LOGS_DIR
    ingest_module.LOGS_DIR = temp_data_dir
    
    test_log = temp_data_dir / "alignment.json"
    
    # Create sample data
    icecube_data = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-04']),
        'muon_count': [100, 101, 103]
    })
    
    era5_data = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-03', '2023-01-04']),
        'level': [1000, 1000, 1000],
        'value': [280, 281, 282]
    })
    
    try:
        aligned_icecube, aligned_era5 = align_temporal_data(icecube_data, era5_data)
        
        # Check that the log file was created and contains the exclusion event
        assert test_log.exists()
        
        with open(test_log, 'r') as f:
            data = json.load(f)
        
        # We expect one exclusion event for 2023-01-02 (missing in era5)
        # and one for 2023-01-03 (missing in icecube)
        # The function logs for all non-common dates
        assert len(data) == 2
    finally:
        ingest_module.LOGS_DIR = original_logs_dir
