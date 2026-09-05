import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.finalize import (
    load_interim_lagged_mmns,
    load_accuracy_blocks,
    load_excluded_subjects,
    filter_by_excluded_subjects,
    validate_aligned_data,
    run_finalization_pipeline
)

@pytest.fixture
def temp_data_setup(tmp_path):
    """
    Create temporary data files required for T026 testing.
    """
    # Create interim_lagged_mmns.csv
    mmn_data = {
        'subject_id': ['S01', 'S01', 'S02', 'S02', 'S03', 'S03'],
        'block_id': [1, 2, 1, 2, 1, 2],
        'mmn_amplitude': [1.5, 1.6, 2.1, 2.2, 1.8, 1.9],
        'source_window_start_trial': [0, 50, 0, 50, 0, 50]
    }
    mmn_df = pd.DataFrame(mmn_data)
    mmn_path = tmp_path / "interim_lagged_mmns.csv"
    mmn_df.to_csv(mmn_path, index=False)

    # Create accuracy_blocks.csv
    acc_data = {
        'subject_id': ['S01', 'S01', 'S02', 'S02', 'S03', 'S03'],
        'block_id': [1, 2, 1, 2, 1, 2],
        'accuracy': [0.85, 0.88, 0.90, 0.92, 0.80, 0.82],
        'trial_start': [10, 60, 10, 60, 10, 60],
        'trial_end': [20, 70, 20, 70, 20, 70]
    }
    acc_df = pd.DataFrame(acc_data)
    acc_path = tmp_path / "accuracy_blocks.csv"
    acc_df.to_csv(acc_path, index=False)

    # Create excluded_subjects.csv (S03 should be excluded)
    exc_data = {
        'subject_id': ['S03'],
        'reason': ['underpowered']
    }
    exc_df = pd.DataFrame(exc_data)
    exc_path = tmp_path / "excluded_subjects.csv"
    exc_df.to_csv(exc_path, index=False)

    return {
        'mmn_path': mmn_path,
        'acc_path': acc_path,
        'exc_path': exc_path,
        'data_dir': tmp_path
    }

def test_t026_merge_logic(temp_data_setup):
    """
    Test that T026 correctly merges MMN and Accuracy data.
    """
    mmn_df = load_interim_lagged_mmns(temp_data_setup['mmn_path'])
    acc_df = load_accuracy_blocks(temp_data_setup['acc_path'])
    
    # Manual merge check
    merged = pd.merge(mmn_df, acc_df, on=['subject_id', 'block_id'], how='inner')
    
    assert len(merged) == 6
    assert 'accuracy' in merged.columns
    assert 'mmn_amplitude' in merged.columns
    assert 'subject_id' in merged.columns

def test_t026_full_pipeline_execution(temp_data_setup):
    """
    Test the full T026 pipeline execution with real file paths.
    Verifies:
    1. Output file is created
    2. Excluded subjects are removed
    3. No NaN values in critical columns
    4. Schema matches requirements
    """
    output_path = run_finalization_pipeline(temp_data_setup['data_dir'])
    
    # Check file exists
    assert output_path.exists(), "aligned_data.csv was not created"
    
    # Load and validate
    result_df = pd.read_csv(output_path)
    
    # Check excluded subjects (S03 should be gone)
    assert 'S03' not in result_df['subject_id'].values, "Excluded subject S03 found in output"
    
    # Check expected subjects remain
    assert 'S01' in result_df['subject_id'].values
    assert 'S02' in result_df['subject_id'].values
    
    # Check row count (should be 4 rows: S01x2, S02x2)
    assert len(result_df) == 4, f"Expected 4 rows, got {len(result_df)}"
    
    # Check schema
    required_cols = ['subject_id', 'block_id', 'mmn_amplitude', 'source_window_start_trial', 'accuracy']
    for col in required_cols:
        assert col in result_df.columns, f"Missing column: {col}"
    
    # Check for NaN in critical columns
    assert result_df['mmn_amplitude'].isna().sum() == 0
    assert result_df['accuracy'].isna().sum() == 0

def test_t026_validation_logic(temp_data_setup):
    """
    Test the validation function specifically.
    """
    # Create a valid dataframe
    valid_df = pd.DataFrame({
        'subject_id': ['S01'],
        'block_id': [1],
        'mmn_amplitude': [1.5],
        'source_window_start_trial': [0],
        'accuracy': [0.85]
    })
    assert validate_aligned_data(valid_df) is True

    # Create an invalid dataframe (missing column)
    invalid_df = pd.DataFrame({
        'subject_id': ['S01'],
        'block_id': [1],
        'mmn_amplitude': [1.5],
        'accuracy': [0.85]
        # Missing source_window_start_trial
    })
    assert validate_aligned_data(invalid_df) is False

    # Create an invalid dataframe (NaN in critical column)
    nan_df = pd.DataFrame({
        'subject_id': ['S01'],
        'block_id': [1],
        'mmn_amplitude': [1.5],
        'source_window_start_trial': [0],
        'accuracy': [np.nan]
    })
    assert validate_aligned_data(nan_df) is False
