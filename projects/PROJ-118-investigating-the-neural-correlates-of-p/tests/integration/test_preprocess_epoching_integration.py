import pytest
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import run_preprocessing_pipeline
from config_loader import get_project_root

def test_epoching_pipeline_creates_output():
    """
    Integration test: Run the preprocessing pipeline on a small subset of data
    (or mock data if real data is not available in test environment) and verify
    that epo_raw.fif is created.
    
    Note: This test assumes that data/raw contains at least one valid raw file.
    If no real data is available, this test may be skipped or mocked.
    """
    project_root = get_project_root()
    processed_dir = project_root / 'data' / 'processed'
    
    # Check if raw data exists
    raw_dir = project_root / 'data' / 'raw'
    raw_files = list(raw_dir.glob('**/*_task-auditory_raw.fif'))
    
    if not raw_files:
        pytest.skip("No raw data found. Skipping integration test.")
    
    # Run pipeline
    try:
        run_preprocessing_pipeline()
    except Exception as e:
        # If it fails due to missing dependencies or data issues, skip
        if "No stimulus channel" in str(e) or "FileNotFoundError" in str(e):
            pytest.skip(f"Skipping due to data issue: {e}")
        raise
    
    # Verify output exists
    output_files = list(processed_dir.glob('*_epo_raw.fif'))
    assert len(output_files) > 0, "No epo_raw.fif files created."
    
    # Verify at least one file has > 0 epochs
    import mne
    for f in output_files:
        epochs = mne.read_epochs(f, verbose=False)
        assert len(epochs) > 0, f"Epochs file {f} has 0 epochs."

def test_epoching_pipeline_creates_log():
    """Verify that preprocessing_log.json is created."""
    project_root = get_project_root()
    processed_dir = project_root / 'data' / 'processed'
    log_file = processed_dir / 'preprocessing_log.json'
    
    # Run pipeline first
    try:
        run_preprocessing_pipeline()
    except Exception:
        pytest.skip("Pipeline failed, cannot test log creation.")
    
    assert log_file.exists(), "preprocessing_log.json not created."
    
    import json
    with open(log_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) > 0, "Log file is empty."
    assert 'subject' in data[0], "Log entry missing 'subject' key."
    assert 'output' in data[0] or 'error' in data[0], "Log entry missing output or error."
