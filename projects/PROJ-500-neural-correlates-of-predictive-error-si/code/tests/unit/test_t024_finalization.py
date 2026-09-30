import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from src.data.finalize import (
    load_interim_lagged_mmns,
    load_accuracy_blocks,
    load_excluded_subjects,
    filter_by_excluded_subjects,
    run_finalization_pipeline,
    validate_aligned_data
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data files."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

def test_load_interim_lagged_mmns(temp_data_dir):
    """Test loading interim lagged MMNs."""
    # Create mock data
    mock_data = pd.DataFrame({
        'subject_id': ['S1', 'S2', 'S3'],
        'block_id': [1, 2, 3],
        'mmn_amplitude': [0.5, 0.6, 0.7],
        'source_window_start_trial': [10, 20, 30]
    })
    mock_file = temp_data_dir / "interim_lagged_mmns.csv"
    mock_data.to_csv(mock_file, index=False)

    df = load_interim_lagged_mmns(temp_data_dir)
    assert df.shape == mock_data.shape
    assert list(df.columns) == list(mock_data.columns)

def test_load_accuracy_blocks(temp_data_dir):
    """Test loading accuracy blocks."""
    mock_data = pd.DataFrame({
        'subject_id': ['S1', 'S2', 'S3'],
        'block_id': [1, 2, 3],
        'accuracy': [0.9, 0.8, 0.85],
        'trial_start': [0, 10, 20],
        'trial_end': [9, 19, 29]
    })
    mock_file = temp_data_dir / "accuracy_blocks.csv"
    mock_data.to_csv(mock_file, index=False)

    df = load_accuracy_blocks(temp_data_dir)
    assert df.shape == mock_data.shape

def test_load_excluded_subjects(temp_data_dir):
    """Test loading power report."""
    mock_data = pd.DataFrame({
        'subject_id': ['S1', 'S2', 'S3'],
        'reason': ['low_trials', 'low_trials', 'ok'],
        'power_status': ['underpowered_primary', 'underpowered_primary', 'powered']
    })
    mock_file = temp_data_dir / "power_report.csv"
    mock_data.to_csv(mock_file, index=False)

    df = load_excluded_subjects(temp_data_dir)
    assert df is not None
    assert 'underpowered_primary' in df['power_status'].values

def test_filter_by_excluded_subjects_error_mode(temp_data_dir):
    """Test filtering in error_signal mode (excludes underpowered_primary)."""
    mmn_df = pd.DataFrame({
        'subject_id': ['S1', 'S2', 'S3', 'S4'],
        'block_id': [1, 2, 3, 4],
        'mmn_amplitude': [0.1, 0.2, 0.3, 0.4],
        'source_window_start_trial': [1, 2, 3, 4]
    })
    acc_df = pd.DataFrame({
        'subject_id': ['S1', 'S2', 'S3', 'S4'],
        'block_id': [1, 2, 3, 4],
        'accuracy': [0.9, 0.8, 0.7, 0.6],
        'trial_start': [0, 1, 2, 3],
        'trial_end': [0, 1, 2, 3]
    })
    power_df = pd.DataFrame({
        'subject_id': ['S1', 'S2', 'S3', 'S4'],
        'power_status': ['underpowered_primary', 'powered', 'underpowered_primary', 'powered']
    })

    mmn_filtered, acc_filtered = filter_by_excluded_subjects(
        mmn_df, acc_df, power_df, analysis_mode="error_signal"
    )

    # S1 and S3 should be excluded
    assert len(mmn_filtered) == 2
    assert 'S1' not in mmn_filtered['subject_id'].values
    assert 'S3' not in mmn_filtered['subject_id'].values
    assert 'S2' in mmn_filtered['subject_id'].values
    assert 'S4' in mmn_filtered['subject_id'].values

def test_filter_by_excluded_subjects_stimulus_mode(temp_data_dir):
    """Test filtering in stimulus_driven mode (includes all)."""
    mmn_df = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'block_id': [1, 2],
        'mmn_amplitude': [0.1, 0.2],
        'source_window_start_trial': [1, 2]
    })
    acc_df = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'block_id': [1, 2],
        'accuracy': [0.9, 0.8],
        'trial_start': [0, 1],
        'trial_end': [0, 1]
    })
    power_df = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'power_status': ['underpowered_primary', 'powered']
    })

    mmn_filtered, acc_filtered = filter_by_excluded_subjects(
        mmn_df, acc_df, power_df, analysis_mode="stimulus_driven"
    )

    # No one should be excluded
    assert len(mmn_filtered) == 2
    assert 'S1' in mmn_filtered['subject_id'].values

def test_run_finalization_pipeline(temp_data_dir):
    """Test the full finalization pipeline."""
    # Setup mock files
    mmn_data = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'block_id': [1, 2],
        'mmn_amplitude': [0.5, 0.6],
        'source_window_start_trial': [10, 20]
    })
    acc_data = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'block_id': [1, 2],
        'accuracy': [0.9, 0.8],
        'trial_start': [0, 10],
        'trial_end': [9, 19]
    })
    power_data = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'power_status': ['powered', 'powered']
    })

    (temp_data_dir / "interim_lagged_mmns.csv").write_text(mmn_data.to_csv(index=False))
    (temp_data_dir / "accuracy_blocks.csv").write_text(acc_data.to_csv(index=False))
    (temp_data_dir / "power_report.csv").write_text(power_data.to_csv(index=False))

    output_path = run_finalization_pipeline(temp_data_dir, analysis_mode="error_signal")

    assert output_path.exists()
    final_df = pd.read_csv(output_path)
    
    # Check schema
    required_cols = ['subject_id', 'block_id', 'mmn_amplitude', 'source_window_start_trial',
                     'accuracy', 'trial_start', 'trial_end', 'learning_phase', 'power_status']
    for col in required_cols:
        assert col in final_df.columns, f"Missing column: {col}"
    
    # Check data integrity
    assert len(final_df) == 2
    assert final_df['subject_id'].tolist() == ['S1', 'S2']
    assert 'learning_phase' in final_df.columns
    assert 'power_status' in final_df.columns

def test_validate_aligned_data():
    """Test the validation function."""
    valid_df = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        'mmn_amplitude': [0.5],
        'source_window_start_trial': [10],
        'accuracy': [0.9],
        'trial_start': [0],
        'trial_end': [9],
        'learning_phase': ['Early'],
        'power_status': ['powered']
    })
    assert validate_aligned_data(valid_df) is True

    invalid_df = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        # Missing mmn_amplitude
        'accuracy': [0.9],
        'trial_start': [0],
        'trial_end': [9],
        'learning_phase': ['Early'],
        'power_status': ['powered']
    })
    assert validate_aligned_data(invalid_df) is False
