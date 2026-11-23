"""
Unit tests for T016: Artifact rejection and underpowered dataset flagging.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.data.preprocess import (
    detect_artifacts,
    reject_artifacts,
    check_trial_count_loss,
    flag_underpowered_subjects,
    write_excluded_subjects_csv,
    update_validation_report,
    preprocess_dataset,
    run_preprocessing_pipeline
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_detect_artifacts():
    """Test artifact detection logic."""
    # Create mock data with some bad epochs
    n_epochs, n_channels, n_times = 100, 64, 500
    epochs_data = np.random.randn(n_epochs, n_channels, n_times) * 1e-6

    # Inject a large artifact in one epoch
    epochs_data[10, :, :] = 200e-6  # 200 microvolts, above default threshold

    bad_epochs = detect_artifacts(epochs_data)

    assert np.sum(bad_epochs) == 1
    assert bad_epochs[10] is True

def test_reject_artifacts():
    """Test artifact rejection logic."""
    n_epochs, n_channels, n_times = 100, 64, 500
    epochs_data = np.random.randn(n_epochs, n_channels, n_times)
    bad_epochs = np.zeros(n_epochs, dtype=bool)
    bad_epochs[10] = True
    bad_epochs[20] = True

    cleaned_data, num_rejected = reject_artifacts(epochs_data, bad_epochs)

    assert cleaned_data.shape[0] == n_epochs - 2
    assert num_rejected == 2

def test_check_trial_count_loss():
    """Test trial count loss calculation."""
    assert check_trial_count_loss(100, 5) is True  # 5% loss
    assert check_trial_count_loss(100, 6) is False  # 6% loss
    assert check_trial_count_loss(100, 0) is True  # 0% loss

def test_flag_underpowered_subjects():
    """Test underpowered dataset flagging."""
    # Dataset with fewer than 20 subjects
    subject_data = {f"sub-{i:03d}": {} for i in range(15)}
    excluded = flag_underpowered_subjects(subject_data)
    assert len(excluded) == 15

    # Dataset with 20 or more subjects
    subject_data = {f"sub-{i:03d}": {} for i in range(25)}
    excluded = flag_underpowered_subjects(subject_data)
    assert len(excluded) == 0

def test_write_excluded_subjects_csv(temp_data_dir):
    """Test writing excluded subjects to CSV."""
    excluded_subjects = [
        ("sub-001", "underpowered_dataset"),
        ("sub-002", "excessive_artifact_rejection")
    ]
    output_path = temp_data_dir / "excluded_subjects.csv"

    write_excluded_subjects_csv(excluded_subjects, output_path)

    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert list(df.columns) == ["subject_id", "reason"]

def test_update_validation_report(temp_data_dir):
    """Test updating validation report."""
    # Create a mock validation report
    report_path = temp_data_dir / "validation_report.json"
    initial_report = {
        "analysis_mode": "error_signal",
        "dataset_info": {"name": "test_dataset"}
    }
    with open(report_path, 'w') as f:
        json.dump(initial_report, f)

    excluded_subjects = [("sub-001", "underpowered_dataset")]

    update_validation_report(temp_data_dir, excluded_subjects, "error_signal")

    with open(report_path, 'r') as f:
        updated_report = json.load(f)

    assert "excluded_subjects" in updated_report
    assert updated_report["excluded_subjects"][0]["subject_id"] == "sub-001"
    assert updated_report["exclusion_summary"]["total_excluded"] == 1

def test_preprocess_dataset_excludes_underpowered_subjects(temp_data_dir):
    """Test that preprocess_dataset correctly excludes underpowered subjects."""
    # Create a mock subject with excessive artifacts
    subject_data = {
        "subject_id": "sub-001",
        "epochs": np.random.randn(100, 64, 500) * 200e-6  # High amplitude, will be rejected
    }

    processed_data, exclusions = preprocess_dataset(subject_data, temp_data_dir, "error_signal")

    assert len(exclusions) == 1
    assert exclusions[0][0] == "sub-001"
    assert exclusions[0][1] == "excessive_artifact_rejection"

def test_preprocess_dataset_flagging_underpowered_dataset(temp_data_dir):
    """Test flagging of underpowered datasets."""
    # Simulate a dataset with only 5 subjects
    all_subjects_data = {f"sub-{i:03d}": {"subject_id": f"sub-{i:03d}", "epochs": np.random.randn(100, 64, 500)} for i in range(5)}

    # Create a mock validation report
    report_path = temp_data_dir / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump({"analysis_mode": "error_signal"}, f)

    run_preprocessing_pipeline(temp_data_dir, "error_signal")

    # Check that all subjects were excluded
    excluded_csv_path = temp_data_dir / "excluded_subjects.csv"
    assert excluded_csv_path.exists()
    df = pd.read_csv(excluded_csv_path)
    assert len(df) == 5
    assert all(df["reason"] == "underpowered_dataset")
