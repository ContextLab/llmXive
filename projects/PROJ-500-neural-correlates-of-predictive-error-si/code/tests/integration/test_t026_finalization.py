import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile

from src.data.finalize import run_finalization_pipeline
from src.data.align import run_lagged_alignment_pipeline, run_behavioral_binning_pipeline
from src.data.preprocess import generate_excluded_subjects_csv


@pytest.fixture
def temp_data_setup():
    """Setup a minimal temp directory with pre-requisite data for T024 integration test."""
    tmpdir = tempfile.mkdtemp()
    data_path = Path(tmpdir)
    
    # Mock preprocessed data (simulating T015/T016 output)
    # We need to create a scenario where T016 generated excluded_subjects.csv
    # and T021/T022 generated the intermediate files.
    
    # 1. Create excluded_subjects.csv (T016 output)
    exc_df = pd.DataFrame({
        'subject_id': ['S_underpowered'],
        'reason': 'Trial count < 500'
    })
    exc_df.to_csv(data_path / "excluded_subjects.csv", index=False)
    
    # 2. Create interim_lagged_mmns.csv (T022 output)
    mmn_df = pd.DataFrame({
        'subject_id': ['S_valid', 'S_valid', 'S_underpowered'],
        'block_id': [1, 2, 1],
        'mmn_amplitude': [1.1, 1.2, 0.9],
        'source_window_start_trial': [0, 10, 0],
        'learning_phase': ['Early', 'Late', 'Early']
    })
    mmn_df.to_csv(data_path / "interim_lagged_mmns.csv", index=False)
    
    # 3. Create accuracy_blocks.csv (T021 output)
    acc_df = pd.DataFrame({
        'subject_id': ['S_valid', 'S_valid', 'S_underpowered'],
        'block_id': [1, 2, 1],
        'accuracy': [0.88, 0.91, 0.50],
        'trial_start': [0, 10, 0],
        'trial_end': [10, 20, 10],
        'trial_count': [500, 500, 300]
    })
    acc_df.to_csv(data_path / "accuracy_blocks.csv", index=False)
    
    return data_path


def test_t026_merge_logic(temp_data_setup):
    """
    Integration test for T024 (Finalization) logic:
    - Verifies that excluded subjects are removed.
    - Verifies that the merge produces the correct schema.
    """
    output_file = run_finalization_pipeline(temp_data_setup)
    
    assert os.path.exists(output_file)
    result = pd.read_csv(output_file)
    
    # Check exclusions
    assert 'S_underpowered' not in result['subject_id'].values
    assert 'S_valid' in result['subject_id'].values
    
    # Check schema
    expected_cols = ['subject_id', 'block_id', 'mmn_amplitude', 'accuracy', 'learning_phase']
    for col in expected_cols:
        assert col in result.columns
    
    # Check row count (2 blocks for S_valid)
    assert len(result) == 2


def test_t026_full_pipeline_execution(temp_data_setup):
    """
    Runs the full sequence from intermediate files to final output.
    """
    # This is effectively what test_t026_merge_logic does, but explicitly
    # checks the return value and file existence as per T024 requirements.
    try:
        path = run_finalization_pipeline(temp_data_setup)
        assert path is not None
        assert os.path.isfile(path)
    except Exception as e:
        pytest.fail(f"Finalization pipeline failed: {e}")


def test_t026_validation_logic(temp_data_setup):
    """
    Tests that validation logic catches data quality issues before writing.
    """
    # Modify the mock data to include a NaN in accuracy
    acc_df = pd.read_csv(temp_data_setup / "accuracy_blocks.csv")
    acc_df.loc[0, 'accuracy'] = None
    acc_df.to_csv(temp_data_setup / "accuracy_blocks.csv", index=False)
    
    # This should raise an error or return False in validation
    from src.data.finalize import validate_aligned_data, load_interim_lagged_mmns, load_accuracy_blocks, filter_by_excluded_subjects, load_excluded_subjects
    
    mmn = load_interim_lagged_mmns(temp_data_setup)
    acc = load_accuracy_blocks(temp_data_setup)
    excluded = load_excluded_subjects(temp_data_setup)
    
    mmn_f, acc_f = filter_by_excluded_subjects(mmn, acc, excluded)
    merged = pd.merge(mmn_f, acc_f, on=['subject_id', 'block_id'], how='inner')
    
    # Validation should fail due to NaN
    assert not validate_aligned_data(merged)
