"""
Integration test for T012: Data Download & Validation.
Verifies that the download pipeline fetches, validates, and logs exclusions correctly.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Mocking the config to use a temporary directory
from unittest.mock import patch, MagicMock
import pandas as pd

from download import run_download_pipeline, write_exclusion_log, filter_dataset_columns

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

def test_filter_dataset_columns_success():
    """Test that valid columns pass validation."""
    df = pd.DataFrame({
        "duration_estimate": [1.0, 2.0],
        "stimulus_sequence": [1, 2],
        "participant_id": [1, 2]
    })
    required = ["duration_estimate", "stimulus_sequence", "participant_id"]
    is_valid, missing = filter_dataset_columns(df, required)
    assert is_valid is True
    assert missing == []

def test_filter_dataset_columns_failure():
    """Test that missing columns fail validation."""
    df = pd.DataFrame({
        "duration_estimate": [1.0, 2.0],
        "other_col": [1, 2]
    })
    required = ["duration_estimate", "stimulus_sequence", "participant_id"]
    is_valid, missing = filter_dataset_columns(df, required)
    assert is_valid is False
    assert "stimulus_sequence" in missing

def test_write_exclusion_log(temp_dir):
    """Test that exclusion log is written correctly."""
    log_path = temp_dir / "exclusion_log.json"
    write_exclusion_log(log_path, "test_ds", "Missing columns")
    
    assert log_path.exists()
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["dataset_id"] == "test_ds"
    assert data[0]["reason"] == "Missing columns"

def test_run_download_pipeline_no_data(temp_dir):
    """Test pipeline halts when no datasets are found."""
    # Create a fake dataset_ids.txt that points to non-existent data
    ids_file = temp_dir / "dataset_ids.txt"
    ids_file.write_text("99999,openml,time_perception\n")
    
    # Mock the fetch functions to raise an error immediately
    from download import fetch_openml_dataset
    
    with patch('download.fetch_openml_dataset') as mock_fetch:
        mock_fetch.side_effect = Exception("Network error")
        
        # We expect the pipeline to run but find 0 valid datasets
        # In the real main(), this would exit(1). Here we test the logic.
        # We need to patch get_data_dir and get_processed_dir to use temp_dir
        from config import get_data_dir, get_processed_dir
        
        # Temporarily override config functions
        original_get_data_dir = get_data_dir
        original_get_processed_dir = get_processed_dir
        
        import code.config as config_module
        config_module.get_data_dir = lambda: temp_dir
        config_module.get_processed_dir = lambda: temp_dir / "processed"
        
        try:
            valid_datasets = run_download_pipeline(ids_file)
            assert len(valid_datasets) == 0
        finally:
            # Restore original functions
            config_module.get_data_dir = original_get_data_dir
            config_module.get_processed_dir = original_get_processed_dir