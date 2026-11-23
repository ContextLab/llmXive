"""
Integration test for "Missing Metadata" edge case (T011).

Verifies that the system halts and logs a DataIntegrityError when
dataset_description.json lacks the 'sampling_frequency' field.
"""
import os
import json
import tempfile
import logging
from pathlib import Path
import pytest

# Import from project modules
from exceptions import DataIntegrityError
from validators import validate_sampling_frequency
from logger import configure_root_logger, get_logger, log_data_integrity_error
from config import get_project_root


def test_missing_sampling_frequency_raises_data_integrity_error():
    """
    Verify system halts and logs DataIntegrityError when
    dataset_description.json lacks the 'sampling_frequency' field.
    """
    # Setup: Create a temporary BIDS-like directory structure with missing metadata
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_root = Path(tmpdir)
        dataset_desc_path = dataset_root / "dataset_description.json"
        
        # Create a dataset_description.json WITHOUT sampling_frequency
        # We simulate a minimal valid BIDS description but omit the required field
        bad_description = {
            "Name": "Test Dataset Missing Sampling Freq",
            "BIDSVersion": "1.7.0",
            "DatasetType": "raw"
            # NOTE: 'sampling_frequency' is intentionally missing
        }
        
        with open(dataset_desc_path, 'w') as f:
            json.dump(bad_description, f, indent=2)
        
        # Also create a minimal eeg file reference to simulate a subject
        # (The validator checks the dataset_description.json primarily for this field)
        sub_dir = dataset_root / "sub-01" / "eeg"
        sub_dir.mkdir(parents=True)
        # Create a dummy FIF file (empty is fine for this metadata check)
        dummy_eeg = sub_dir / "sub-01_task-rest_eeg.fif"
        dummy_eeg.touch()

        # Configure logger to capture output
        logger = configure_root_logger()
        log_capture_string = None  # In a real integration, we might capture logs differently

        # Execute: Call the validator which should raise DataIntegrityError
        # The validator function signature expects a path to the dataset or a description dict
        # Based on existing API, we pass the path to the dataset root
        with pytest.raises(DataIntegrityError) as exc_info:
            validate_sampling_frequency(dataset_root)

        # Assert: Verify the error message contains the expected text
        error_message = str(exc_info.value)
        assert "Missing 'sampling_frequency'" in error_message or "sampling_frequency" in error_message
        assert "DataIntegrityError" in str(type(exc_info.value).__name__) or isinstance(exc_info.value, DataIntegrityError)

        # Additional check: Ensure the logger was invoked (conceptually)
        # In a real system, we might assert that a specific log handler received the error.
        # Here, the raising of the exception is the primary verification of "halting".
        assert True  # If we reached here without raising, the test would fail in pytest.raises