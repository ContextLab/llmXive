"""
Unit tests for T016: Artifact rejection and underpowered subject flagging.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.data.preprocess import (
    calculate_artifact_rejection_rate,
    validate_trial_count_loss,
    identify_underpowered_subjects,
    write_excluded_subjects_csv,
    update_validation_report,
    preprocess_dataset
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()
        yield {
            'data_dir': data_dir,
            'output_dir': output_dir,
            'tmpdir': Path(tmpdir)
        }


def test_calculate_artifact_rejection_rate():
    """Test artifact rejection rate calculation."""
    assert calculate_artifact_rejection_rate(100, 5) == 5.0
    assert calculate_artifact_rejection_rate(100, 0) == 0.0
    assert calculate_artifact_rejection_rate(100, 10) == 10.0
    assert calculate_artifact_rejection_rate(0, 0) == 0.0


def test_validate_trial_count_loss():
    """Test trial count loss validation."""
    # Valid case: 5% loss
    is_valid, loss = validate_trial_count_loss(100, 95)
    assert is_valid is True
    assert loss == 5.0

    # Invalid case: 6% loss
    is_valid, loss = validate_trial_count_loss(100, 94)
    assert is_valid is False
    assert loss == 6.0

    # Edge case: exactly at threshold
    is_valid, loss = validate_trial_count_loss(100, 95)
    assert is_valid is True


def test_identify_underpowered_subjects():
    """Test identification of underpowered subjects."""
    subject_counts = {
        'sub-001': 50,
        'sub-002': 15,
        'sub-003': 25,
        'sub-004': 10,
        'sub-005': 30
    }

    underpowered = identify_underpowered_subjects(subject_counts, threshold=20)
    assert set(underpowered) == {'sub-002', 'sub-004'}


def test_write_excluded_subjects_csv(temp_data_dir):
    """Test writing excluded subjects to CSV."""
    output_path = temp_data_dir['output_dir'] / "excluded_subjects.csv"
    excluded_subjects = ['sub-001', 'sub-002', 'sub-003']

    write_excluded_subjects_csv(excluded_subjects, output_path)

    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 3
    assert list(df['subject_id']) == excluded_subjects
    assert all(df['reason'] == 'underpowered')


def test_update_validation_report(temp_data_dir):
    """Test updating validation report with underpowered subjects."""
    report_path = temp_data_dir['output_dir'] / "validation_report.json"
    underpowered = ['sub-001', 'sub-002']

    update_validation_report(report_path, underpowered)

    assert report_path.exists()
    with open(report_path, 'r') as f:
        report = json.load(f)

    assert report['underpowered_subjects'] == underpowered
    assert report['underpowered_count'] == 2
    assert report['validation_status'] == 'warning'


def test_preprocess_dataset_excludes_underpowered_subjects(temp_data_dir):
    """Test that preprocess_dataset correctly identifies and excludes underpowered subjects."""
    # Create mock subject data files
    data_dir = temp_data_dir['data_dir']

    # Create subjects with varying trial counts
    subjects_data = [
        {'subject_id': 'sub-001', 'original_trial_count': 100, 'final_trial_count': 95},
        {'subject_id': 'sub-002', 'original_trial_count': 50, 'final_trial_count': 15},  # Underpowered
        {'subject_id': 'sub-003', 'original_trial_count': 80, 'final_trial_count': 75},
        {'subject_id': 'sub-004', 'original_trial_count': 60, 'final_trial_count': 10},  # Underpowered
        {'subject_id': 'sub-005', 'original_trial_count': 90, 'final_trial_count': 85},
    ]

    for i, subj_data in enumerate(subjects_data):
        file_path = data_dir / f"subject_{i}.json"
        with open(file_path, 'w') as f:
            json.dump(subj_data, f)

    # Run preprocessing
    results = preprocess_dataset(
        data_dir=data_dir,
        output_dir=temp_data_dir['output_dir'],
        validation_report_path=temp_data_dir['output_dir'] / "validation_report.json"
    )

    # Verify results
    assert results['total_subjects'] == 5
    assert len(results['excluded_subjects']) == 2
    assert set(results['excluded_subjects']) == {'sub-002', 'sub-004'}

    # Verify CSV was written
    excluded_csv = temp_data_dir['output_dir'] / "excluded_subjects.csv"
    assert excluded_csv.exists()
    df = pd.read_csv(excluded_csv)
    assert len(df) == 2


def test_preprocess_dataset_flagging_underpowered_dataset(temp_data_dir):
    """Test that the validation report is correctly updated with underpowered subjects."""
    data_dir = temp_data_dir['data_dir']

    # Create subjects where most are underpowered
    subjects_data = [
        {'subject_id': 'sub-001', 'original_trial_count': 100, 'final_trial_count': 15},
        {'subject_id': 'sub-002', 'original_trial_count': 50, 'final_trial_count': 10},
        {'subject_id': 'sub-003', 'original_trial_count': 80, 'final_trial_count': 5},
    ]

    for i, subj_data in enumerate(subjects_data):
        file_path = data_dir / f"subject_{i}.json"
        with open(file_path, 'w') as f:
            json.dump(subj_data, f)

    # Run preprocessing
    results = preprocess_dataset(
        data_dir=data_dir,
        output_dir=temp_data_dir['output_dir'],
        validation_report_path=temp_data_dir['output_dir'] / "validation_report.json"
    )

    # Verify validation report
    report_path = temp_data_dir['output_dir'] / "validation_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)

    assert report['underpowered_count'] == 3
    assert report['validation_status'] == 'warning'
    assert len(report['underpowered_subjects']) == 3
