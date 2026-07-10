"""
Integration test for the full download and preprocess pipeline (User Story 1).

This test verifies the end-to-end flow:
1. Data acquisition (Auditory ds000246)
2. Validation (Sampling rate >= 500Hz, Trial counts)
3. Preprocessing (Filtering, ICA, Re-referencing)
4. Artifact generation (Cleaned data file)

It uses real data from OpenNeuro as mandated by the project constraints.
"""
import os
import tempfile
import pytest
from pathlib import Path
import numpy as np
import mne

# Import project modules
from code.config.env_config import get_env_config
from code.data.data_loader import validate_sampling_rate, validate_trial_counts, DataLoaderError
from code.utils.logger import get_logger
from code.data.download import download_auditory_dataset
from code.data.preprocess import preprocess_raw_data

logger = get_logger(__name__)

# Configuration for test limits (stricter than prod to ensure CI feasibility)
# In a real CI environment, we might use a subset or a specific subject if the full download is too large.
# However, the task requires "Real Data". We will attempt to download the full dataset.
# If the dataset is too large for the CI environment (e.g., > 7GB RAM), this test might need to be
# split into smaller unit tests for specific functions, but this file represents the integration logic.

# Note: ds000246 is the Auditory Oddball dataset.
# We will target a single subject (e.g., 'sub-01') to keep runtime manageable for integration testing
# while still exercising the real pipeline.
TEST_SUBJECT = 'sub-01'
TEST_DATASET = 'ds000246'

@pytest.fixture(scope="module")
def test_config():
    """Load configuration for the test."""
    # Ensure we have a config, even if no .env is present
    try:
        cfg = get_env_config()
    except Exception:
        # Fallback to defaults if env config fails (e.g., missing .env)
        from code.config import get_config
        cfg = get_config()
    return cfg

@pytest.fixture(scope="module")
def test_output_dir(tmp_path_factory):
    """Create a temporary directory for test outputs."""
    return tmp_path_factory.mktemp("pipeline_test_output")

@pytest.mark.integration
def test_full_pipeline_auditory(test_config, test_output_dir):
    """
    Integration test: Download -> Validate -> Preprocess -> Save.
    
    This test ensures that the real data from OpenNeuro can be fetched,
    validated against the project constraints (sampling rate, trial counts),
    preprocessed, and saved as a valid FIF file.
    """
    logger.info("Starting integration test for Auditory Pipeline (ds000246)")
    
    # 1. Download Data
    # We download to the temp directory to avoid polluting the project data folder during tests
    download_dir = test_output_dir / "raw"
    download_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading dataset {TEST_DATASET}...")
    # download_auditory_dataset handles the mne.datasets.fetch call
    raw_path = download_auditory_dataset(
        dataset_name=TEST_DATASET,
        target_dir=str(download_dir),
        subject_ids=[TEST_SUBJECT]
    )
    
    assert raw_path is not None, "Download failed to return a path"
    assert os.path.exists(raw_path), f"Downloaded file not found at {raw_path}"
    logger.info(f"Downloaded data to: {raw_path}")
    
    # 2. Load Raw Data for Validation
    # MNE loads .fif, .edf, etc. The download function should return the path to the raw file.
    try:
        raw = mne.io.read_raw_fif(raw_path, preload=False)
    except Exception as e:
        # If it's not a FIF file, try reading as generic (MNE handles extensions)
        # But ds000246 is typically FIF. Let's try to be robust.
        logger.warning(f"Could not read as FIF directly: {e}. Attempting generic read.")
        # If the path points to a directory (common in OpenNeuro), we need to find the file.
        # The download function should ideally return the specific file path.
        # If it returns a directory, we scan for .fif or .edf.
        if os.path.isdir(raw_path):
            # Find the first raw file
            for ext in ['.fif', '.edf', '.vhdr']:
                for f in Path(raw_path).rglob(f'*{ext}'):
                    if 'raw' in f.name.lower():
                        raw_path = str(f)
                        break
            raw = mne.io.read_raw_fif(raw_path, preload=False)
        else:
            raise e
    
    # 3. Validation
    logger.info("Validating sampling rate...")
    sfreq = raw.info['sfreq']
    logger.info(f"Sampling rate found: {sfreq} Hz")
    
    # Validate against config threshold (default >= 500 Hz)
    try:
        validate_sampling_rate(sfreq, min_hz=test_config.SAMPLING_RATE_MIN)
        logger.info("Sampling rate validation PASSED")
    except DataLoaderError as e:
        pytest.fail(f"Sampling rate validation failed: {e}")
    
    logger.info("Validating trial counts...")
    # Extract events to count trials
    # ds000246 uses event codes. We need to identify 'standard' and 'oddball'.
    # Typically: 1 = standard, 2 = oddball (or similar). We'll check for event presence.
    events, event_dict = mne.events_from_annotations(raw)
    
    if len(events) == 0:
        # Try to infer from stim channel if annotations are missing
        # For ds000246, annotations are usually present.
        logger.warning("No events found in annotations. Attempting to read from stim channel.")
        # This is a fallback; real implementation might be more specific
        pass
    
    # Count specific trial types based on standard OpenNeuro ds000246 codes
    # Code 1: Standard, Code 2: Oddball (Target)
    # We need at least 100 oddball and 300 standard.
    # Note: In a real run, we might need to adjust these codes based on the specific dataset version.
    # For ds000246, the events are usually in the annotations.
    
    trial_counts = {}
    for event in events:
        val = event[2]
        trial_counts[val] = trial_counts.get(val, 0) + 1
    
    # Map generic codes to 'standard' and 'oddball' if possible, or check counts directly
    # Assuming standard OpenNeuro mapping: 1=Standard, 2=Oddball
    standard_count = trial_counts.get(1, 0) + trial_counts.get(3, 0) # Sometimes 3 is also standard
    oddball_count = trial_counts.get(2, 0)
    
    # If the counts are low, try to look for other common codes
    if oddball_count < 100:
        # Fallback: count all events as trials if specific codes aren't found (less strict for integration test)
        # But the task requires specific validation.
        # Let's assume the dataset is correct and just validate the counts we found.
        pass
    
    logger.info(f"Trial counts - Standard: {standard_count}, Oddball: {oddball_count}")
    
    try:
        validate_trial_counts(
            standard_count=standard_count,
            oddball_count=oddball_count,
            min_standard=test_config.MIN_STANDARD_TRIALS,
            min_oddball=test_config.MIN_ODDBALL_TRIALS
        )
        logger.info("Trial count validation PASSED")
    except DataLoaderError as e:
        # If validation fails, it might be due to specific subject selection in CI.
        # We will log the error but proceed if it's a known dataset issue, or fail the test.
        # For strict compliance, we fail.
        pytest.fail(f"Trial count validation failed: {e}")
    
    # 4. Preprocessing
    logger.info("Starting preprocessing...")
    raw.load_data() # Preload for processing
    
    # Apply bandpass filter (e.g., 0.1 - 30 Hz)
    raw = raw.filter(l_freq=0.1, h_freq=30.0, n_jobs=1)
    
    # Run ICA
    ica = mne.preprocessing.ICA(method='fastica', random_state=42, n_components=0.99)
    ica.fit(raw)
    
    # Find and remove EOG artifacts (simple heuristic for integration test)
    # In a full pipeline, we would use find_bads_eog
    eog_indices, _ = ica.find_bads_eog(raw)
    ica.exclude = eog_indices
    ica.apply(raw)
    
    # Re-reference (Common Average)
    raw = raw.set_eeg_average_ref()
    
    logger.info("Preprocessing completed.")
    
    # 5. Save Output
    output_path = test_output_dir / "processed" / "cleaned_data.fif"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    raw.save(output_path, overwrite=True)
    logger.info(f"Saved cleaned data to {output_path}")
    
    # 6. Verification
    assert os.path.exists(output_path), "Output file was not created"
    
    # Verify the file can be read back
    raw_check = mne.io.read_raw_fif(output_path, preload=False)
    assert raw_check.info['sfreq'] == raw.info['sfreq'], "Sampling rate mismatch in saved file"
    
    logger.info("Integration test PASSED: Full pipeline executed successfully.")
    
@pytest.mark.integration
def test_pipeline_validation_failure_low_sfreq(test_config, test_output_dir):
    """
    Integration test: Verify that the pipeline halts with an error if sampling rate is too low.
    We simulate this by creating a mock raw object or modifying the validation logic call.
    Since we can't easily download a low-sfreq dataset, we test the validation function directly
    in an integration context.
    """
    # This is a hybrid integration/unit test to ensure the validation logic is wired correctly.
    # We call the validation function with a low sampling rate.
    with pytest.raises(DataLoaderError):
        validate_sampling_rate(sfreq=250.0, min_hz=test_config.SAMPLING_RATE_MIN)
        
    logger.info("Validation failure test PASSED: Correctly rejected low sampling rate.")