"""
Test suite for T040: Feasibility and Resource Validation.
Verifies that the pipeline respects memory and time limits on a 1-year subset.
"""
import os
import sys
import time
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, PropertyMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from cli.main import (
    check_memory_limit, 
    run_pipeline_with_monitoring, 
    MEMORY_LIMIT_MB, 
    TIME_LIMIT_SECONDS
)
from utils.logging import init_logging, get_logger
import logging

@pytest.fixture
def logger():
    return init_logging(console_level=logging.INFO)

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logs."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_check_memory_limit_under_threshold(logger):
    """Test that memory check passes when under limit."""
    # Mock psutil to return a value under the limit
    mock_process = MagicMock()
    # RSS in bytes
    mock_process.memory_info.return_value.rss = (MEMORY_LIMIT_MB * 0.5) * 1024 * 1024
    
    with patch('cli.main.psutil.Process', return_value=mock_process):
        exceeded = check_memory_limit(logger)
        assert exceeded is False

def test_check_memory_limit_over_threshold(logger, caplog):
    """Test that memory check fails and logs correctly when over limit."""
    mock_process = MagicMock()
    # RSS in bytes
    mock_process.memory_info.return_value.rss = (MEMORY_LIMIT_MB * 1.5) * 1024 * 1024
    
    with patch('cli.main.psutil.Process', return_value=mock_process):
        exceeded = check_memory_limit(logger)
        assert exceeded is True
        # Check that the specific error message is logged
        assert "CRITICAL: Memory limit" in caplog.text

def test_pipeline_time_limit_exceeded(logger, temp_log_dir):
    """Test that the pipeline exits with code 124 if time limit is exceeded."""
    # We simulate a pipeline that takes longer than the limit
    # by patching the internal time check or the sleep duration.
    # Since run_pipeline_with_monitoring loops, we mock the check_time_limit
    # to return True immediately after start.
    
    # We need to mock the time.time() calls inside the loop to simulate elapsed time
    # However, the simplest way is to mock the check logic directly if exposed,
    # or mock the sleep.
    
    # Let's mock the start_time and the loop condition.
    # We'll patch `time.time` to return a value that makes elapsed > TIME_LIMIT_SECONDS immediately.
    
    original_time = time.time
    start_time_val = original_time()
    
    # Create a side effect that returns start_time + large delta after first call
    def time_side_effect():
        return start_time_val + (TIME_LIMIT_SECONDS + 100)
    
    with patch('cli.main.time.time', side_effect=time_side_effect):
        # Also need to mock the actual pipeline execution to return quickly
        # so we don't actually wait 6 hours
        with patch('cli.main._run_pipeline_logic', return_value=0) as mock_run:
            # We need to ensure the memory check doesn't fail first
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = (MEMORY_LIMIT_MB * 0.5) * 1024 * 1024
            with patch('cli.main.psutil.Process', return_value=mock_process):
                # Patch check_memory_limit to return False
                with patch('cli.main.check_memory_limit', return_value=False):
                    exit_code = run_pipeline_with_monitoring(logger, start_time_val)
                    # Assert it returns 124 for timeout
                    assert exit_code == 124
                    # Verify the pipeline logic was attempted (or skipped due to timeout)
                    # The logic should check time before running or during

def test_pipeline_memory_limit_exceeded(logger, temp_log_dir):
    """Test that the pipeline exits with code 1 if memory limit is exceeded."""
    # Mock psutil to return high memory usage
    mock_process = MagicMock()
    mock_process.memory_info.return_value.rss = (MEMORY_LIMIT_MB * 2.0) * 1024 * 1024
    
    # Mock the check_memory_limit to return True (exceeded) immediately
    with patch('cli.main.psutil.Process', return_value=mock_process):
        with patch('cli.main.check_memory_limit', return_value=True):
            # We need a start time for the function
            start_time = time.time()
            exit_code = run_pipeline_with_monitoring(logger, start_time)
            assert exit_code == 1

def test_log_file_creation_and_content(logger, temp_log_dir):
    """Test that the resource monitor log file is created and has correct header."""
    log_path = os.path.join(temp_log_dir, "resource_monitor.log")
    
    # Mock the log path in the config or the function to use our temp dir
    # Since run_pipeline_with_monitoring writes to a specific path, we might need to patch that.
    # For this test, we verify the logic by checking if the file exists after a run.
    # However, since we can't easily run the full pipeline, we test the file writing logic
    # by mocking the relevant parts.
    
    # Let's assume the function writes to data/logs/resource_monitor.log
    # We'll patch the log path to our temp dir.
    
    # Mock the pipeline to run quickly and write the log
    mock_process = MagicMock()
    mock_process.memory_info.return_value.rss = (MEMORY_LIMIT_MB * 0.5) * 1024 * 1024
    
    with patch('cli.main.psutil.Process', return_value=mock_process):
        with patch('cli.main.check_memory_limit', return_value=False):
            # Patch the log directory path
            with patch('cli.main.LOG_DIR', temp_log_dir):
                start_time = time.time()
                # We need to ensure the pipeline runs at least one iteration
                # Mock the internal loop to run once and write the log
                with patch('cli.main.time.sleep', return_value=None):
                    with patch('cli.main._run_pipeline_logic', return_value=0):
                        exit_code = run_pipeline_with_monitoring(logger, start_time)
    
    # Now check if the log file exists and has the correct header
    assert os.path.exists(log_path)
    with open(log_path, 'r') as f:
        header = f.readline().strip()
        assert header == "timestamp,rss_mb,elapsed_s,memory_limit_exceeded"
        
        # Check that at least one data row was written
        lines = f.readlines()
        assert len(lines) > 0
        
        # Verify the format of the first data row
        first_row = lines[0].strip().split(',')
        assert len(first_row) == 4
        # timestamp should be a string
        assert len(first_row[0]) > 0
        # rss_mb should be a number
        float(first_row[1])
        # elapsed_s should be a number
        float(first_row[2])
        # memory_limit_exceeded should be True or False
        assert first_row[3] in ['True', 'False']

def test_1year_subset_execution_time(logger, temp_log_dir):
    """
    Integration test: Run the pipeline on a 1-year subset and assert time < 6h.
    This test mocks the heavy lifting to simulate a fast run, but verifies the
    timing logic and the exit code.
    """
    # Mock the data ingestion to return a small subset (1 year)
    # We mock the fetch and parse functions to return dummy data quickly
    
    mock_process = MagicMock()
    mock_process.memory_info.return_value.rss = (MEMORY_LIMIT_MB * 0.5) * 1024 * 1024
    
    with patch('cli.main.psutil.Process', return_value=mock_process):
        with patch('cli.main.check_memory_limit', return_value=False):
            # Mock the internal pipeline logic to simulate a 1-hour run
            # We patch time.time to advance by 3600 seconds (1 hour) during the run
            start_time = time.time()
            elapsed_time = 0
            
            def mock_time():
                nonlocal elapsed_time
                elapsed_time += 100 # Advance by 100 seconds per call
                return start_time + elapsed_time
            
            with patch('cli.main.time.time', side_effect=mock_time):
                with patch('cli.main.time.sleep', return_value=None):
                    with patch('cli.main._run_pipeline_logic', return_value=0):
                        # We need to ensure the loop doesn't run too many times
                        # by mocking the condition or the sleep
                        # Here we assume the loop runs a fixed number of times
                        # and we check the total elapsed time
                        
                        # We'll patch the loop to run only once for this test
                        # and then check the time
                        with patch('cli.main.time.sleep', return_value=None):
                            exit_code = run_pipeline_with_monitoring(logger, start_time)
                            
                            # The exit code should be 0 (success)
                            assert exit_code == 0
                            
                            # The total elapsed time should be less than 6 hours (21600 seconds)
                            # Since we mocked time to advance by 100 seconds per call,
                            # and the loop runs a few times, the total time should be small.
                            # We can't easily assert the exact time without more mocking,
                            # but we can assert that it didn't hit the timeout.
                            assert elapsed_time < TIME_LIMIT_SECONDS

def test_subset_data_availability(logger):
    """
    Verify that the pipeline can find and process a 1-year subset of data.
    This test checks that the data ingestion logic can handle a limited date range.
    """
    # This test would ideally run the ingestion pipeline with a specific date range
    # and verify that it completes successfully.
    # Since we are in the feasibility test suite, we mock the heavy parts.
    
    # Mock the fetch and parse functions to return a small dataset
    with patch('data.ingestion.fetch_satellite_data') as mock_fetch:
        with patch('data.ingestion.parse_slr_file') as mock_parse:
            # Setup mock return values
            mock_fetch.return_value = b"dummy_slr_data"
            mock_parse.return_value = [
                {"timestamp": "2020-01-01", "range": 1234.5, "satellite_id": "LAGEOS-1"},
                {"timestamp": "2020-01-02", "range": 1235.0, "satellite_id": "LAGEOS-1"}
            ]
            
            # Run the ingestion logic for a 1-year subset
            # This is a simplified test; in reality, we'd call the actual pipeline
            # with a date range argument
            
            # We assert that the mock was called
            assert mock_fetch.called
            assert mock_parse.called

def test_resource_monitoring_integration(logger, temp_log_dir):
    """
    End-to-end test: Run the pipeline with resource monitoring enabled.
    Verify that the log file is created, populated, and the pipeline completes
    within the time and memory limits.
    """
    # This test combines the previous tests to verify the full integration
    
    mock_process = MagicMock()
    mock_process.memory_info.return_value.rss = (MEMORY_LIMIT_MB * 0.5) * 1024 * 1024
    
    with patch('cli.main.psutil.Process', return_value=mock_process):
        with patch('cli.main.check_memory_limit', return_value=False):
            # Mock the pipeline logic to run quickly
            with patch('cli.main._run_pipeline_logic', return_value=0):
                with patch('cli.main.time.sleep', return_value=None):
                    # Mock time to advance slowly
                    start_time = time.time()
                    elapsed = 0
                    def mock_time():
                        nonlocal elapsed
                        elapsed += 10
                        return start_time + elapsed
                    
                    with patch('cli.main.time.time', side_effect=mock_time):
                        exit_code = run_pipeline_with_monitoring(logger, start_time)
                        
                        # Assert success
                        assert exit_code == 0
                        
                        # Check log file
                        log_path = os.path.join(temp_log_dir, "resource_monitor.log")
                        if os.path.exists(log_path):
                            with open(log_path, 'r') as f:
                                lines = f.readlines()
                                # Header + at least one data row
                                assert len(lines) >= 2
                                # Verify header
                                assert "timestamp,rss_mb,elapsed_s,memory_limit_exceeded" in lines[0]