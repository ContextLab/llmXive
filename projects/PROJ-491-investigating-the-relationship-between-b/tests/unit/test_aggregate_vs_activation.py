import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
import csv

# Import the functions to test
from aggregate_vs_activation import (
    calculate_mean_activation,
    write_activation_csv,
    find_valid_subject_dirs
)

class TestCalculateMeanActivation:
    def test_mean_of_positive_values(self):
        ts = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = calculate_mean_activation(ts)
        assert result == 3.0

    def test_mean_of_negative_values(self):
        ts = np.array([-1.0, -2.0, -3.0])
        result = calculate_mean_activation(ts)
        assert result == -2.0

    def test_mean_of_zeros(self):
        ts = np.zeros(10)
        result = calculate_mean_activation(ts)
        assert result == 0.0

    def test_mean_with_nan_input(self):
        # If input is None or empty, should return nan
        result = calculate_mean_activation(None)
        assert np.isnan(result)
        
        result = calculate_activation(np.array([]))
        assert np.isnan(result)

    def test_mean_single_value(self):
        ts = np.array([42.0])
        result = calculate_mean_activation(ts)
        assert result == 42.0

class TestWriteActivationCsv:
    def test_write_csv_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            data = [("sub-001", 1.5), ("sub-002", 2.5)]
            
            write_activation_csv(data, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                assert rows[0] == ['subject_id', 'mean_activation']
                assert rows[1] == ['sub-001', '1.5']
                assert rows[2] == ['sub-002', '2.5']

    def test_write_csv_empty_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_output.csv"
            data = []
            
            write_activation_csv(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                # Should have header only
                assert len(rows) == 1
                assert rows[0] == ['subject_id', 'mean_activation']

class TestFindValidSubjectDirs:
    def test_find_valid_subjects_in_mock_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create a valid subject structure
            sub_dir = base / "sub-001" / "MNINonLinear" / "Results"
            sub_dir.mkdir(parents=True)
            # Create a dummy nifti
            (sub_dir / "task-rest_bold.nii.gz").touch()
            
            # Create an invalid subject (no nifti)
            bad_sub_dir = base / "sub-002" / "MNINonLinear" / "Results"
            bad_sub_dir.mkdir(parents=True)
            
            # Create a non-subject folder
            (base / "random_folder").mkdir()

            valid = find_valid_subject_dirs(base)
            
            assert len(valid) == 1
            assert valid[0].name == "sub-001"

    def test_find_valid_subjects_no_raw_dir(self):
        # Should return empty list if raw dir doesn't exist
        valid = find_valid_subject_dirs(Path("/nonexistent/path"))
        assert len(valid) == 0