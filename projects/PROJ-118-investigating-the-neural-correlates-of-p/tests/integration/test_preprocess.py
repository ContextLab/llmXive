"""
Integration test for User Story 1: Preprocess Auditory Oddball EEG Data.

Task: T011
Description: Run pipeline on sub-01, assert data/processed/epo_raw.fif exists 
             and contains >0 epochs.
"""
import os
import glob
import pytest
from pathlib import Path

# Import the real pipeline entry point from the project's code module
from code.preprocess import run_preprocessing_pipeline
from code.download import run_download_pipeline
from code.config import load_config

# Project root relative to this file (assuming tests/integration/ is 2 levels deep)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist (setup handled by T001/T004, but safe-guard here)
@pytest.fixture(scope="module", autouse=True)
def ensure_directories():
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

def test_preprocess_pipeline_sub_01():
    """
    Integration test: Run the full preprocessing pipeline on sub-01.
    
    Steps:
    1. Ensure raw data exists (fetch if missing via download module).
    2. Run preprocessing pipeline.
    3. Assert output file 'data/processed/epo_raw.fif' exists.
    4. Assert the file contains >0 epochs for 'standard' and 'deviant' conditions.
    """
    import mne

    # 1. Ensure Raw Data Exists
    # We attempt to find a raw file for sub-01. If not found, we trigger the download.
    # The download module is expected to place files in data/raw/ds003645/...
    # We look for typical BIDS or OpenNeuro patterns.
    raw_files = list(DATA_RAW.glob("**/sub-01*_desc-raw.fif"))
    if not raw_files:
        # Fallback: try to find any sub-01 raw file regardless of suffix
        raw_files = list(DATA_RAW.glob("**/sub-01*.fif"))
    
    if not raw_files:
        # If still nothing, try to trigger the download pipeline for the dataset
        # Assuming config is set up to download ds003645
        try:
            run_download_pipeline()
            raw_files = list(DATA_RAW.glob("**/sub-01*.fif"))
        except Exception as e:
            pytest.fail(f"Could not locate raw data for sub-01 and download failed: {e}")

    if not raw_files:
        pytest.fail("No raw data files found for sub-01 after download attempt.")

    # Pick the first valid raw file found
    raw_input_path = raw_files[0]

    # 2. Run Preprocessing Pipeline
    # We call the main entry point. It should handle:
    # - Loading the raw file
    # - Subsampling, filtering, re-referencing
    # - ICA cleaning
    # - Epoching
    # - Saving to data/processed/epo_raw.fif
    
    output_path = DATA_PROCESSED / "epo_raw.fif"
    
    # Remove existing output if any to ensure fresh run
    if output_path.exists():
        output_path.unlink()

    try:
        run_preprocessing_pipeline(input_path=raw_input_path, output_path=output_path)
    except Exception as e:
        pytest.fail(f"Preprocessing pipeline failed for sub-01: {e}")

    # 3. Assert Output File Exists
    assert output_path.exists(), f"Output file {output_path} was not created."

    # 4. Assert Content: >0 Epochs
    try:
        epochs = mne.read_epochs(output_path, preload=False)
    except Exception as e:
        pytest.fail(f"Failed to read epochs from {output_path}: {e}")

    # Check total number of epochs
    total_epochs = len(epochs)
    assert total_epochs > 0, f"Epochs file is empty (0 epochs) for sub-01."

    # Check specific conditions
    # The task requires 'standard' and 'deviant' labels
    event_ids = epochs.event_id
    assert "standard" in event_ids, "Condition 'standard' not found in epochs."
    assert "deviant" in event_ids, "Condition 'deviant' not found in epochs."

    standard_count = len(epochs["standard"])
    deviant_count = len(epochs["deviant"])

    assert standard_count > 0, f"No 'standard' epochs found for sub-01 (count: {standard_count})."
    assert deviant_count > 0, f"No 'deviant' epochs found for sub-01 (count: {deviant_count})."

    # Optional: Verify some basic properties (e.g., time window)
    assert epochs.times[0] < 0, "Pre-stimulus baseline not present."
    assert epochs.times[-1] > 0, "Post-stimulus window not present."

    print(f"✅ Test Passed: sub-01 processed successfully.")
    print(f"   Total epochs: {total_epochs}")
    print(f"   Standard epochs: {standard_count}")
    print(f"   Deviant epochs: {deviant_count}")