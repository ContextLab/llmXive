import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path

from src.data.finalize import (
    load_interim_lagged_mmns,
    load_accuracy_blocks,
    load_excluded_subjects,
    filter_by_excluded_subjects,
    validate_aligned_data,
    run_finalization_pipeline
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock data files for T024 testing."""
    tmpdir = tempfile.mkdtemp()
    data_path = Path(tmpdir)
    
    # Mock interim_lagged_mmns.csv
    mmn_data = pd.DataFrame({
        'subject_id': ['S1', 'S1', 'S2', 'S2', 'S3'],
        'block_id': [1, 2, 1, 2, 1],
        'mmn_amplitude': [1.2, 1.5, 2.0, 2.1, 0.8],
        'source_window_start_trial': [0, 10, 0, 10, 0],
        'learning_phase': ['Early', 'Late', 'Early', 'Late', 'Early']
    })
    mmn_data.to_csv(data_path / "interim_lagged_mmns.csv", index=False)
    
    # Mock accuracy_blocks.csv
    acc_data = pd.DataFrame({
        'subject_id': ['S1', 'S1', 'S2', 'S2', 'S3'],
        'block_id': [1, 2, 1, 2, 1],
        'accuracy': [0.85, 0.90, 0.70, 0.75, 0.60],
        'trial_start': [0, 10, 0, 10, 0],
        'trial_end': [10, 20, 10, 20, 10],
        'trial_count': [500, 500, 400, 400, 600]  # S2 has <500 trials
    })
    acc_data.to_csv(data_path / "accuracy_blocks.csv", index=False)
    
    # Mock excluded_subjects.csv (S3 excluded for other reasons, S2 excluded for power)
    exc_data = pd.DataFrame({
        'subject_id': ['S3', 'S2'],
        'reason': ['Artifact', 'Low Trial Count']
    })
    exc_data.to_csv(data_path / "excluded_subjects.csv", index=False)
    
    return data_path


def test_load_interim_lagged_mmns(temp_data_dir):
    df = load_interim_lagged_mmns(temp_data_dir)
    assert len(df) == 5
    assert 'mmn_amplitude' in df.columns


def test_load_accuracy_blocks(temp_data_dir):
    df = load_accuracy_blocks(temp_data_dir)
    assert len(df) == 5
    assert 'accuracy' in df.columns


def test_load_excluded_subjects(temp_data_dir):
    excluded = load_excluded_subjects(temp_data_dir)
    assert 'S3' in excluded
    assert 'S2' in excluded


def test_filter_by_excluded_subjects(temp_data_dir):
    mmn = load_interim_lagged_mmns(temp_data_dir)
    acc = load_accuracy_blocks(temp_data_dir)
    excluded = load_excluded_subjects(temp_data_dir)
    
    mmn_f, acc_f = filter_by_excluded_subjects(mmn, acc, excluded)
    
    assert len(mmn_f) == 2  # Only S1 remains
    assert len(acc_f) == 2
    assert 'S2' not in mmn_f['subject_id'].values
    assert 'S3' not in acc_f['subject_id'].values


def test_validate_aligned_data_success(temp_data_dir):
    # Create a valid merged dataset
    mmn = load_interim_lagged_mmns(temp_data_dir)
    acc = load_accuracy_blocks(temp_data_dir)
    excluded = load_excluded_subjects(temp_data_dir)
    
    mmn_f, acc_f = filter_by_excluded_subjects(mmn, acc, excluded)
    merged = pd.merge(mmn_f, acc_f, on=['subject_id', 'block_id'], how='inner')
    
    # Add trial_count to merged for validation
    # Note: In real flow, trial_count comes from acc_df
    assert validate_aligned_data(merged) is True


def test_validate_aligned_data_failure_low_trials(temp_data_dir):
    # Create a dataset with a row violating trial count
    mmn = load_interim_lagged_mmns(temp_data_dir)
    acc = load_accuracy_blocks(temp_data_dir)
    excluded = load_excluded_subjects(temp_data_dir)
    
    mmn_f, acc_f = filter_by_excluded_subjects(mmn, acc, excluded)
    merged = pd.merge(mmn_f, acc_f, on=['subject_id', 'block_id'], how='inner')
    
    # Inject a violation (though filter_by_excluded_subjects removed S2 which had low trials)
    # We manually add a row with low trials to test validation logic
    bad_row = pd.DataFrame({
        'subject_id': ['S4'],
        'block_id': [99],
        'mmn_amplitude': [1.0],
        'learning_phase': ['Early'],
        'accuracy': [0.5],
        'trial_start': [0],
        'trial_end': [10],
        'trial_count': [100]  # Violation
    })
    merged = pd.concat([merged, bad_row], ignore_index=True)
    
    assert validate_aligned_data(merged) is False


def test_run_finalization_pipeline(temp_data_dir):
    output_path = run_finalization_pipeline(temp_data_dir)
    
    assert os.path.exists(output_path)
    df = pd.read_csv(output_path)
    
    # Verify content
    assert len(df) == 2  # Only S1 blocks
    assert 'subject_id' in df.columns
    assert 'accuracy' in df.columns
    assert 'mmn_amplitude' in df.columns
    assert 'learning_phase' in df.columns
    
    # Verify no excluded subjects
    assert 'S2' not in df['subject_id'].values
    assert 'S3' not in df['subject_id'].values
    
    # Verify no NaNs
    assert df.isna().sum().sum() == 0
