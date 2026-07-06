import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from src.data.preprocess import preprocess_dataset, load_config, get_subject_list_from_data, compute_trial_counts_by_subject

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        # Create some fake subject directories
        for i in range(25):
            subject_dir = data_dir / f"sub-{i:03d}"
            subject_dir.mkdir()
            # Create a fake raw data file
            (subject_dir / "raw.fif").touch()
        yield data_dir

def test_preprocess_dataset_excludes_underpowered_subjects(temp_data_dir):
    """Test that subjects with too few trials are excluded."""
    output_dir = temp_data_dir.parent / "output"
    output_dir.mkdir()

    # Mock the get_subject_list_from_data function to return a list of subjects
    # We need to patch the function in the preprocess module
    import src.data.preprocess as preprocess_module

    original_get_subject_list = preprocess_module.get_subject_list_from_data
    def mock_get_subject_list(data_dir):
        return [f"sub-{i:03d}" for i in range(25)]
    preprocess_module.get_subject_list_from_data = mock_get_subject_list

    # Mock compute_trial_counts_by_subject to return low trial counts for some subjects
    original_compute_trial_counts = preprocess_module.compute_trial_counts_by_subject
    def mock_compute_trial_counts(raw_data_path):
        # Return low trial counts for subjects 0-4
        subject_id = raw_data_path.name
        if subject_id.startswith("sub-00") or subject_id.startswith("sub-01"):
            return 5  # Low trial count
        return 100  # Normal trial count
    preprocess_module.compute_trial_counts_by_subject = mock_compute_trial_counts

    try:
        result = preprocess_dataset("ds000001", temp_data_dir, output_dir)

        # Check that subjects with low trial counts are excluded
        assert "sub-000" in result["excluded_subjects"]
        assert "sub-001" in result["excluded_subjects"]
        assert "sub-000" in result["underpowered_subjects"]
        assert "sub-001" in result["underpowered_subjects"]

        # Check that the excluded_subjects.csv file is created
        excluded_subjects_path = output_dir / "excluded_subjects.csv"
        assert excluded_subjects_path.exists()

        # Check that the validation_report.json file is updated
        validation_report_path = output_dir / "validation_report.json"
        assert validation_report_path.exists()

        with open(validation_report_path, 'r') as f:
            validation_report = json.load(f)

        assert "sub-000" in validation_report["underpowered_subjects"]
        assert "sub-001" in validation_report["underpowered_subjects"]
    finally:
        # Restore original functions
        preprocess_module.get_subject_list_from_data = original_get_subject_list
        preprocess_module.compute_trial_counts_by_subject = original_compute_trial_counts

def test_preprocess_dataset_flagging_underpowered_dataset(temp_data_dir):
    """Test that the dataset is flagged as underpowered if total subjects < 20."""
    output_dir = temp_data_dir.parent / "output2"
    output_dir.mkdir()

    import src.data.preprocess as preprocess_module

    # Mock get_subject_list_from_data to return only 15 subjects
    def mock_get_subject_list(data_dir):
        return [f"sub-{i:03d}" for i in range(15)]
    preprocess_module.get_subject_list_from_data = mock_get_subject_list

    # Mock compute_trial_counts_by_subject to return normal trial counts
    def mock_compute_trial_counts(raw_data_path):
        return 100
    preprocess_module.compute_trial_counts_by_subject = mock_compute_trial_counts

    try:
        result = preprocess_dataset("ds000001", temp_data_dir, output_dir)

        # Check that all subjects are flagged as underpowered
        assert len(result["underpowered_subjects"]) == 15
        assert len(result["excluded_subjects"]) == 15

        # Check that the validation_report.json file is updated
        validation_report_path = output_dir / "validation_report.json"
        with open(validation_report_path, 'r') as f:
            validation_report = json.load(f)

        assert len(validation_report["underpowered_subjects"]) == 15
    finally:
        # Restore original functions
        preprocess_module.get_subject_list_from_data = lambda x: [f"sub-{i:03d}" for i in range(25)]
        preprocess_module.compute_trial_counts_by_subject = lambda x: 100
