"""
Unit tests for T049: Full Pipeline Integration Test.
These tests verify the orchestration logic without running the full 6-hour pipeline.
"""
import os
import json
import tempfile
import time
from unittest.mock import patch, MagicMock
import pytest

# Import the main function from the script
from code.main import (
    ensure_directories,
    ensure_sample_data,
    validate_outputs,
    MAX_EXECUTION_TIME_SECONDS
)

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the STATE_DIR constant
        with patch('code.main.STATE_DIR', tmpdir):
            yield tmpdir

def test_ensure_directories_creates_folders(temp_state_dir):
    """Test that ensure_directories creates the required folders."""
    from code.main import ensure_directories
    
    # Verify state dir exists (created by fixture)
    assert os.path.exists(temp_state_dir)
    
    # Call function (should not raise)
    ensure_directories()
    
    # Verify subdirectories
    assert os.path.exists(os.path.join(temp_state_dir, "data", "processed"))
    assert os.path.exists(os.path.join(temp_state_dir, "data", "raw"))

def test_validate_outputs_fails_on_missing_files(temp_state_dir):
    """Test that validate_outputs raises FileNotFoundError for missing files."""
    from code.main import validate_outputs
    
    # Create a fake processed dir but no files
    os.makedirs(os.path.join(temp_state_dir, "data", "processed"), exist_ok=True)
    
    # Patch the function to look in our temp dir
    with patch('code.main.VALIDATION_LOG_PATH', os.path.join(temp_state_dir, "log.json")):
        with patch('code.main.os.path.exists', side_effect=lambda p: p == temp_state_dir or p.endswith("validation_log.json")):
            with pytest.raises(FileNotFoundError) as excinfo:
                validate_outputs()
            
            assert "Required output files missing" in str(excinfo.value)

def test_validate_outputs_passes_on_all_files(temp_state_dir):
    """Test that validate_outputs passes when all files exist."""
    # Create required files
    processed_dir = os.path.join(temp_state_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    required_files = [
        "descriptors.csv",
        "model_results.json",
        "sensitivity_analysis.json",
        "analysis_summary.json",
        "feature_importance.csv",
        "corr_plot_top5.png"
    ]
    
    for f in required_files:
        with open(os.path.join(processed_dir, f), 'w') as fp:
            fp.write("dummy")
    
    # Mock os.path.exists to return True for these specific files
    original_exists = os.path.exists
    def mock_exists(path):
        if path.endswith(tuple(required_files)):
            return True
        return original_exists(path)
    
    with patch('code.main.os.path.exists', side_effect=mock_exists):
        # Should not raise
        try:
            validate_outputs()
        except FileNotFoundError:
            pytest.fail("validate_outputs raised unexpectedly")

@patch('code.main.run_descriptors')
@patch('code.main.run_training')
@patch('code.main.run_sensitivity')
@patch('code.main.run_vif')
@patch('code.main.run_analysis_summary')
@patch('code.main.run_plotting')
def test_run_full_pipeline_calls_all_stages(mock_plot, mock_summary, mock_vif, mock_sens, mock_train, mock_desc):
    """Test that run_full_pipeline calls all stage functions."""
    from code.main import run_full_pipeline
    
    run_full_pipeline()
    
    mock_desc.assert_called_once()
    mock_train.assert_called_once()
    mock_sens.assert_called_once()
    mock_vif.assert_called_once()
    mock_summary.assert_called_once()
    mock_plot.assert_called_once()

@patch('code.main.run_full_pipeline')
@patch('code.main.validate_outputs')
@patch('code.main.ensure_directories')
@patch('code.main.ensure_sample_data')
def test_main_success_path(mock_data, mock_dirs, mock_validate, mock_run, temp_state_dir):
    """Test the main function on a successful run."""
    from code.main import main
    
    # Mock time to ensure we pass the time check
    with patch('code.main.time.time', side_effect=[0, 100]):  # 100 seconds < 6 hours
        with patch('code.main.MAX_EXECUTION_TIME_SECONDS', 3600):
            # Should not raise
            try:
                main()
            except SystemExit as e:
                if e.code != 0:
                    pytest.fail(f"Main exited with code {e.code}")
    
    # Verify log file was created
    log_path = os.path.join(temp_state_dir, "validation_log.json")
    assert os.path.exists(log_path)
    with open(log_path) as f:
        log_data = json.load(f)
    
    assert log_data["status"] == "PASS"
    assert log_data["task_id"] == "T049"