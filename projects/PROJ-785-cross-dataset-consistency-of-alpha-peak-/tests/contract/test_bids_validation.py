"""
Contract test for BIDS validation in the cross-dataset APF consistency pipeline.

This module contains write-first contract tests that verify the BIDS validation
logic, specifically testing that missing critical metadata raises appropriate errors.

User Story: US1 - Data Acquisition and Dual-Pipeline Preprocessing
Task ID: T007
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

# Import the exception we expect to be raised
from exceptions import DataIntegrityError

# Import the validator function we are testing
# Note: We are testing validate_sampling_frequency which is expected to be in validators.py
from validators import validate_sampling_frequency


class TestValidateSamplingFrequency:
    """Contract tests for validate_sampling_frequency function."""
    
    def test_validate_sampling_frequency_raises(self):
        """
        Assert that a missing 'sampling_frequency' in dataset_description.json 
        raises DataIntegrityError.
        
        This is a contract test that verifies the system fails loudly when
        critical BIDS metadata is missing, as required by the specification.
        """
        # Create a temporary directory structure mimicking a BIDS dataset
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            
            # Create a dataset_description.json WITHOUT sampling_frequency
            # This simulates a malformed BIDS dataset
            dataset_desc = {
                "Name": "Test Dataset Without Sampling Frequency",
                "BIDSVersion": "1.7.0",
                "DatasetType": "raw"
                # Note: sampling_frequency is intentionally missing
            }
            
            desc_path = dataset_root / "dataset_description.json"
            with open(desc_path, "w") as f:
                json.dump(dataset_desc, f)
            
            # Create a minimal eeg directory structure
            sub_dir = dataset_root / "sub-01" / "eeg"
            sub_dir.mkdir(parents=True)
            
            # Create a dummy eeg file
            eeg_file = sub_dir / "sub-01_task-rest_eeg.fif"
            eeg_file.touch()
            
            # Also create a corresponding channels.tsv to make it slightly more realistic
            # (though the error should trigger before we even look at this)
            channels_file = sub_dir / "sub-01_task-rest_channels.tsv"
            with open(channels_file, "w") as f:
                f.write("name\ttype\tunits\n")
                f.write("Cz\tEEG\tV\n")
            
            # Create sidecar JSON for the EEG file
            eeg_json = sub_dir / "sub-01_task-rest_eeg.json"
            with open(eeg_json, "w") as f:
                json.dump({
                    "TaskName": "rest"
                    # Note: SamplingFrequency is missing here too
                }, f)
            
            # Now test that validate_sampling_frequency raises DataIntegrityError
            # We need to pass the path to the dataset root
            with pytest.raises(DataIntegrityError) as exc_info:
                validate_sampling_frequency(dataset_root)
            
            # Verify the error message contains relevant information
            error_message = str(exc_info.value)
            assert "sampling_frequency" in error_message.lower() or "missing" in error_message.lower(), \
                f"Error message should mention missing sampling_frequency: {error_message}"
            
            # Verify the exception type is specifically DataIntegrityError
            assert isinstance(exc_info.value, DataIntegrityError)
    
    def test_validate_sampling_frequency_passes(self):
        """
        Assert that a valid dataset_description.json WITH sampling_frequency 
        does NOT raise an error.
        
        This is a negative test to ensure we don't have false positives.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            
            # Create a valid dataset_description.json WITH sampling_frequency
            dataset_desc = {
                "Name": "Test Dataset With Sampling Frequency",
                "BIDSVersion": "1.7.0",
                "DatasetType": "raw",
                "SamplingFrequency": 256.0
            }
            
            desc_path = dataset_root / "dataset_description.json"
            with open(desc_path, "w") as f:
                json.dump(dataset_desc, f)
            
            # Create minimal directory structure
            sub_dir = dataset_root / "sub-01" / "eeg"
            sub_dir.mkdir(parents=True)
            
            # Create dummy files
            (sub_dir / "sub-01_task-rest_eeg.fif").touch()
            (sub_dir / "sub-01_task-rest_channels.tsv").write_text("name\ttype\tunits\nCz\tEEG\tV\n")
            (sub_dir / "sub-01_task-rest_eeg.json").write_text('{"TaskName": "rest", "SamplingFrequency": 256.0}')
            
            # This should NOT raise an exception
            result = validate_sampling_frequency(dataset_root)
            
            # Verify the function returns successfully (result should be True or None)
            assert result is True or result is None, \
                f"validate_sampling_frequency should return True or None for valid data, got: {result}"