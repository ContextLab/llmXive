import os
import json
import numpy as np
import pytest
from pathlib import Path

# Mock the dependencies if not available in test environment
# But we assume the code is tested in an environment where nibabel/numpy are present
import nibabel as nib

class TestT014Extraction:
    """
    Tests for T014: Extract BOLD timecourses for Left Hippocampus.
    Verifies existence and basic structure of the output file.
    """

    def test_output_file_exists(self):
        """Verify that the output file roi_left_hipp.npy exists."""
        output_path = Path("data/processed/roi_left_hipp.npy")
        assert output_path.exists(), f"Output file {output_path} does not exist. T014 failed to produce artifact."

    def test_output_file_not_empty(self):
        """Verify that the output file is not empty and can be loaded."""
        output_path = Path("data/processed/roi_left_hipp.npy")
        if output_path.exists():
            try:
                data = np.load(output_path, allow_pickle=True)
                assert data.size > 0, "Output array is empty."
                assert data.ndim == 2, f"Expected 2D array, got {data.ndim}D."
            except Exception as e:
                pytest.fail(f"Failed to load or validate output file: {e}")
        else:
            pytest.skip("Output file does not exist yet.")

    def test_ids_file_exists(self):
        """Verify that the companion subject IDs file exists."""
        ids_path = Path("data/processed/roi_left_hipp.ids.json")
        assert ids_path.exists(), f"Companion file {ids_path} does not exist."

    def test_ids_file_valid_json(self):
        """Verify that the subject IDs file contains valid JSON."""
        ids_path = Path("data/processed/roi_left_hipp.ids.json")
        if ids_path.exists():
            try:
                with open(ids_path, 'r') as f:
                    ids = json.load(f)
                assert isinstance(ids, list), "Subject IDs should be a list."
                assert len(ids) > 0, "Subject IDs list is empty."
            except Exception as e:
                pytest.fail(f"Invalid JSON in subject IDs file: {e}")
        else:
            pytest.skip("IDs file does not exist yet.")

    def test_shape_consistency(self):
        """Verify that the number of subjects in the array matches the IDs file."""
        output_path = Path("data/processed/roi_left_hipp.npy")
        ids_path = Path("data/processed/roi_left_hipp.ids.json")
        
        if output_path.exists() and ids_path.exists():
            data = np.load(output_path, allow_pickle=True)
            with open(ids_path, 'r') as f:
                ids = json.load(f)
            
            assert data.shape[0] == len(ids), \
                f"Mismatch: Array has {data.shape[0]} rows but IDs file has {len(ids)} entries."
        else:
            pytest.skip("Required files do not exist yet.")

    def test_data_types(self):
        """Verify that the data is float32 as expected."""
        output_path = Path("data/processed/roi_left_hipp.npy")
        if output_path.exists():
            data = np.load(output_path, allow_pickle=True)
            assert data.dtype == np.float32, f"Expected float32, got {data.dtype}"
        else:
            pytest.skip("Output file does not exist yet.")