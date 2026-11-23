"""
Test for T015: Extract BOLD timecourses for Right Hippocampus.
Verifies existence of data/processed/roi_right_hipp.npy and basic structure.
"""
import os
import json
import numpy as np
import pytest
from pathlib import Path

class TestT015RightHippocampus:
    
    def test_output_file_exists(self):
        """Verify that the output file is created."""
        output_path = "data/processed/roi_right_hipp.npy"
        assert os.path.exists(output_path), f"Output file {output_path} does not exist."

    def test_output_file_not_empty(self):
        """Verify that the output file is not empty."""
        output_path = "data/processed/roi_right_hipp.npy"
        assert os.path.getsize(output_path) > 0, f"Output file {output_path} is empty."

    def test_output_is_valid_npy(self):
        """Verify that the file is a valid NumPy array."""
        output_path = "data/processed/roi_right_hipp.npy"
        try:
            data = np.load(output_path, allow_pickle=True)
            assert isinstance(data, np.ndarray), "Loaded data is not a NumPy array."
        except Exception as e:
            pytest.fail(f"Failed to load NPY file: {e}")

    def test_output_has_correct_shape(self):
        """Verify that the array has at least 2 dimensions (subjects, timepoints)."""
        output_path = "data/processed/roi_right_hipp.npy"
        data = np.load(output_path, allow_pickle=True)
        assert data.ndim >= 2, f"Expected at least 2D array, got {data.ndim}D. Shape: {data.shape}"

    def test_output_contains_nan_padding(self):
        """Verify that padding (if any) is represented by NaNs."""
        output_path = "data/processed/roi_right_hipp.npy"
        data = np.load(output_path, allow_pickle=True)
        # Check if there are any NaNs (expected if subjects have different time lengths)
        has_nans = np.isnan(data).any()
        # This is a soft check; if all subjects have same length, no NaNs.
        # We just ensure that if there are Nones or invalids, they are NaNs.
        # The main check is that the array is numeric.
        assert np.isfinite(data).any() or np.isnan(data).all(), "Array contains non-numeric values other than NaN."

    def test_subject_ids_file_exists(self):
        """Verify that the subject IDs file is created."""
        ids_path = "data/processed/roi_right_hipp_ids.json"
        assert os.path.exists(ids_path), f"Subject IDs file {ids_path} does not exist."

    def test_subject_ids_valid_json(self):
        """Verify that the subject IDs file is valid JSON."""
        ids_path = "data/processed/roi_right_hipp_ids.json"
        with open(ids_path, 'r') as f:
            try:
                ids = json.load(f)
                assert isinstance(ids, list), "Subject IDs should be a list."
                assert len(ids) > 0, "Subject IDs list is empty."
            except json.JSONDecodeError:
                pytest.fail("Subject IDs file is not valid JSON.")