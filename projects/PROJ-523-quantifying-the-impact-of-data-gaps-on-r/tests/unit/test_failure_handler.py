"""
Unit tests for the convergence failure handling module.

Tests FR-008: Add convergence failure handling: log failure, record gap config,
exclude from analysis.
"""
import os
import json
import csv
import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Import the module under test
from gap_filling.failure_handler import (
    log_convergence_failure,
    record_excluded_realization,
    handle_convergence_failure,
    get_excluded_realization_ids,
    is_realization_excluded,
    run_failure_handler_pipeline,
    FAILURE_LOG_FILE,
    EXCLUDED_REALIZATIONS_FILE
)


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test artifacts."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    # Create necessary subdirectories
    os.makedirs(os.path.join(temp_dir, "data", "results"), exist_ok=True)
    
    # Temporarily change the working directory
    os.chdir(temp_dir)
    
    # We need to patch the module-level constants to use temp directory
    import gap_filling.failure_handler as fh_module
    original_failure_file = fh_module.FAILURE_LOG_FILE
    original_excluded_file = fh_module.EXCLUDED_REALIZATIONS_FILE
    
    fh_module.FAILURE_LOG_FILE = "data/results/convergence_failures.json"
    fh_module.EXCLUDED_REALIZATIONS_FILE = "data/results/excluded_realizations.csv"
    
    yield temp_dir
    
    # Restore original values
    fh_module.FAILURE_LOG_FILE = original_failure_file
    fh_module.EXCLUDED_REALIZATIONS_FILE = original_excluded_file
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)


def test_log_convergence_failure_creates_file(temp_test_dir):
    """Test that log_convergence_failure creates the failure log file."""
    failure_record = log_convergence_failure(
        realization_id="test_001",
        algo_name="harmonic_interpolation",
        gap_fraction=0.15,
        gap_morphology="clustered",
        error_message="Test error message",
        exec_time_sec=10.5
    )
    
    # Check that the file was created
    failure_log_path = Path(FAILURE_LOG_FILE)
    assert failure_log_path.exists(), "Failure log file should be created"
    
    # Check the content
    with open(failure_log_path, 'r') as f:
        log_data = json.load(f)
    
    assert "failures" in log_data
    assert len(log_data["failures"]) == 1
    
    failure = log_data["failures"][0]
    assert failure["realization_id"] == "test_001"
    assert failure["algorithm"]["name"] == "harmonic_interpolation"
    assert failure["gap_configuration"]["fraction"] == 0.15
    assert failure["gap_configuration"]["morphology"] == "clustered"
    assert failure["error"]["message"] == "Test error message"
    assert failure["execution_time_sec"] == 10.5
    assert failure["status"] == "CONVERGENCE_FAILURE"
    assert "timestamp" in failure


def test_log_convergence_failure_appends(temp_test_dir):
    """Test that multiple failures are appended to the log."""
    log_convergence_failure(
        realization_id="test_001",
        algo_name="harmonic_interpolation",
        gap_fraction=0.15,
        gap_morphology="clustered",
        error_message="First error",
        exec_time_sec=10.5
    )
    
    log_convergence_failure(
        realization_id="test_002",
        algo_name="wiener_filter",
        gap_fraction=0.20,
        gap_morphology="random",
        error_message="Second error",
        exec_time_sec=15.2
    )
    
    failure_log_path = Path(FAILURE_LOG_FILE)
    with open(failure_log_path, 'r') as f:
        log_data = json.load(f)
    
    assert len(log_data["failures"]) == 2
    
    # Verify both entries
    assert log_data["failures"][0]["realization_id"] == "test_001"
    assert log_data["failures"][1]["realization_id"] == "test_002"


def test_record_excluded_realization_creates_csv(temp_test_dir):
    """Test that record_excluded_realization creates the CSV file."""
    record_excluded_realization(
        realization_id="test_001",
        algo_name="harmonic_interpolation",
        gap_fraction=0.15,
        gap_morphology="clustered",
        reason="CONVERGENCE_FAILURE"
    )
    
    excluded_path = Path(EXCLUDED_REALIZATIONS_FILE)
    assert excluded_path.exists(), "Excluded realizations CSV should be created"
    
    # Check content
    with open(excluded_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    row = rows[0]
    assert row["realization_id"] == "test_001"
    assert row["algorithm"] == "harmonic_interpolation"
    assert row["gap_fraction"] == "0.15"
    assert row["gap_morphology"] == "clustered"
    assert row["reason"] == "CONVERGENCE_FAILURE"
    assert "excluded_at" in row


def test_handle_convergence_failure_logs_and_records(temp_test_dir):
    """Test that handle_convergence_failure both logs and records exclusion."""
    try:
        raise Exception("Simulated convergence failure")
    except Exception as e:
        result = handle_convergence_failure(
            exception=e,
            realization_id="test_003",
            algo_name="iterative_synthesis",
            gap_fraction=0.25,
            gap_morphology="point_source",
            exec_time_sec=20.0
        )
    
    # Check return value
    assert result["status"] == "EXCLUDED"
    assert result["realization_id"] == "test_003"
    assert result["reason"] == "CONVERGENCE_FAILURE"
    assert "failure_record" in result
    
    # Check that failure was logged
    failure_log_path = Path(FAILURE_LOG_FILE)
    assert failure_log_path.exists()
    with open(failure_log_path, 'r') as f:
        log_data = json.load(f)
    assert len(log_data["failures"]) == 1
    
    # Check that exclusion was recorded
    excluded_path = Path(EXCLUDED_REALIZATIONS_FILE)
    assert excluded_path.exists()
    with open(excluded_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["realization_id"] == "test_003"


def test_get_excluded_realization_ids(temp_test_dir):
    """Test loading excluded realization IDs."""
    # First, add some excluded realizations
    record_excluded_realization("test_001", "algo1", 0.15, "random")
    record_excluded_realization("test_002", "algo2", 0.20, "clustered")
    record_excluded_realization("test_003", "algo3", 0.25, "point_source")
    
    excluded_ids = get_excluded_realization_ids()
    
    assert len(excluded_ids) == 3
    assert "test_001" in excluded_ids
    assert "test_002" in excluded_ids
    assert "test_003" in excluded_ids


def test_is_realization_excluded(temp_test_dir):
    """Test checking if a realization is excluded."""
    record_excluded_realization("test_001", "algo1", 0.15, "random")
    
    assert is_realization_excluded("test_001") is True
    assert is_realization_excluded("test_002") is False


def test_run_failure_handler_pipeline(temp_test_dir):
    """Test the pipeline summary function."""
    # Add some test data
    log_convergence_failure(
        "test_001", "algo1", 0.15, "random", "Error 1", 10.0
    )
    record_excluded_realization("test_001", "algo1", 0.15, "random")
    
    summary = run_failure_handler_pipeline()
    
    assert summary["failure_log_exists"] is True
    assert summary["excluded_csv_exists"] is True
    assert summary["total_failures"] == 1
    assert summary["excluded_count"] == 1


def test_multiple_failures_same_realization(temp_test_dir):
    """Test that multiple failures for the same realization are handled correctly."""
    # Log first failure
    log_convergence_failure(
        "test_001", "algo1", 0.15, "random", "First error", 10.0
    )
    
    # Log second failure for same realization
    log_convergence_failure(
        "test_001", "algo2", 0.20, "clustered", "Second error", 15.0
    )
    
    failure_log_path = Path(FAILURE_LOG_FILE)
    with open(failure_log_path, 'r') as f:
        log_data = json.load(f)
    
    # Should have 2 entries
    assert len(log_data["failures"]) == 2
    
    # Both should have the same realization_id
    assert log_data["failures"][0]["realization_id"] == "test_001"
    assert log_data["failures"][1]["realization_id"] == "test_001"
    
    # But different algorithms
    assert log_data["failures"][0]["algorithm"]["name"] == "algo1"
    assert log_data["failures"][1]["algorithm"]["name"] == "algo2"
