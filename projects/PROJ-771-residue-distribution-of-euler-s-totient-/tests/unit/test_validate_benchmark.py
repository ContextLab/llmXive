"""
Unit tests for T032c: validate_benchmark.py
"""
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, mock_open

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from exceptions import BenchmarkFailure
from validate_benchmark import validate_benchmark_result, STATUS_FILE, BENCHMARK_FILE

def test_validate_benchmark_pass():
    """Test that a valid benchmark under the limit passes."""
    # Create a temporary directory for test artifacts
    test_dir = tempfile.mkdtemp()
    results_dir = os.path.join(test_dir, "results", "reports")
    os.makedirs(results_dir)
    
    # Mock file paths
    mock_benchmark_path = os.path.join(results_dir, "benchmark_N5M.json")
    mock_status_path = os.path.join(results_dir, "benchmark_status.json")
    
    # Write a mock benchmark file that passes
    mock_data = {"elapsed_time_seconds": 3000.0} # 50 mins
    with open(mock_benchmark_path, 'w') as f:
        json.dump(mock_data, f)
    
    # Patch the global constants in the module to use our temp dir
    import validate_benchmark
    original_benchmark_file = validate_benchmark.BENCHMARK_FILE
    original_status_file = validate_benchmark.STATUS_FILE
    
    validate_benchmark.BENCHMARK_FILE = mock_benchmark_path
    validate_benchmark.STATUS_FILE = mock_status_path

    try:
        result = validate_benchmark_result()
        assert result is True
        
        # Verify status file was written
        assert os.path.exists(mock_status_path)
        with open(mock_status_path, 'r') as f:
            status = json.load(f)
        assert status["status"] == "passed"
    finally:
        # Restore original paths
        validate_benchmark.BENCHMARK_FILE = original_benchmark_file
        validate_benchmark.STATUS_FILE = original_status_file
        shutil.rmtree(test_dir)

def test_validate_benchmark_fail():
    """Test that a benchmark over the limit raises BenchmarkFailure."""
    test_dir = tempfile.mkdtemp()
    results_dir = os.path.join(test_dir, "results", "reports")
    os.makedirs(results_dir)
    
    mock_benchmark_path = os.path.join(results_dir, "benchmark_N5M.json")
    mock_status_path = os.path.join(results_dir, "benchmark_status.json")
    
    # Write a mock benchmark file that fails (2 hours)
    mock_data = {"elapsed_time_seconds": 7200.0}
    with open(mock_benchmark_path, 'w') as f:
        json.dump(mock_data, f)
    
    import validate_benchmark
    original_benchmark_file = validate_benchmark.BENCHMARK_FILE
    original_status_file = validate_benchmark.STATUS_FILE
    
    validate_benchmark.BENCHMARK_FILE = mock_benchmark_path
    validate_benchmark.STATUS_FILE = mock_status_path

    try:
        try:
            validate_benchmark_result()
            assert False, "Expected BenchmarkFailure to be raised"
        except BenchmarkFailure as e:
            assert e.elapsed_time == 7200.0
            assert e.limit == 3600.0
            
            # Verify failure status file was written by the main logic if called via main,
            # but validate_benchmark_result raises directly. 
            # The test for file writing on failure happens in test_validate_benchmark_fail_status
    finally:
        validate_benchmark.BENCHMARK_FILE = original_benchmark_file
        validate_benchmark.STATUS_FILE = original_status_file
        shutil.rmtree(test_dir)

def test_validate_benchmark_file_not_found():
    """Test that missing benchmark file raises FileNotFoundError."""
    test_dir = tempfile.mkdtemp()
    results_dir = os.path.join(test_dir, "results", "reports")
    os.makedirs(results_dir)
    
    mock_benchmark_path = os.path.join(results_dir, "benchmark_N5M.json")
    mock_status_path = os.path.join(results_dir, "benchmark_status.json")
    
    import validate_benchmark
    original_benchmark_file = validate_benchmark.BENCHMARK_FILE
    original_status_file = validate_benchmark.STATUS_FILE
    
    validate_benchmark.BENCHMARK_FILE = mock_benchmark_path
    validate_benchmark.STATUS_FILE = mock_status_path

    try:
        try:
            validate_benchmark_result()
            assert False, "Expected FileNotFoundError to be raised"
        except FileNotFoundError:
            pass # Expected
    finally:
        validate_benchmark.BENCHMARK_FILE = original_benchmark_file
        validate_benchmark.STATUS_FILE = original_status_file
        shutil.rmtree(test_dir)