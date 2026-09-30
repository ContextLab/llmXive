"""
Unit tests for T022: Lagged Alignment logic.
"""
import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

from src.data.align import run_lagged_alignment_pipeline, add_learning_phase
from src.utils.config import get_data_dir

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data files."""
    tmp_dir = tempfile.mkdtemp()
    # Mock get_data_dir to return this temp dir
    # We monkey patch the function or set an env var if the config uses one
    # For now, we assume the config respects a DATA_DIR env var or we pass paths directly
    original_data_dir = os.environ.get('DATA_DIR')
    os.environ['DATA_DIR'] = tmp_dir
    yield tmp_dir
    if original_data_dir:
        os.environ['DATA_DIR'] = original_data_dir
    else:
        del os.environ['DATA_DIR']
    shutil.rmtree(tmp_dir)

def test_lagged_alignment_schema_and_logic(temp_data_dir):
    """
    Test that run_lagged_alignment_pipeline produces the correct schema and logic.
    """
    # Setup mock data
    # MMN Epochs: subject_id, trial_id, block_id, mmn_amplitude
    mmn_data = {
        'subject_id': ['S1'] * 100,
        'trial_id': list(range(100)),
        'block_id': [0] * 100,
        'mmn_amplitude': np.random.randn(100) * 0.5
    }
    mmn_df = pd.DataFrame(mmn_data)
    
    # Accuracy Blocks: subject_id, block_id, accuracy, trial_start, trial_end
    # Block 0: trials 0-9, Block 1: trials 10-19, etc.
    # We need enough trials to have a source window (t-50 to t-10) for a target block.
    # Let's create 3 blocks.
    # Block 0: trials 0-9. Source window for this would be negative, so likely skipped.
    # Block 1: trials 10-19. Source window: -40 to -1 (skipped).
    # Block 2: trials 20-29. Source window: -30 to -10 (skipped).
    # We need to shift trial IDs to be higher so source window exists.
    
    # Let's create data where Block 10 starts at trial 100.
    # Source window: 100-50=50 to 100-10=90.
    # We need MMN data for trials 50-89.
    
    mmn_data_shifted = {
        'subject_id': ['S1'] * 100,
        'trial_id': list(range(50, 150)), # 50 to 149
        'block_id': [0] * 100,
        'mmn_amplitude': np.random.randn(100) * 0.5
    }
    mmn_df_shifted = pd.DataFrame(mmn_data_shifted)
    
    # Accuracy Blocks
    # Block 0: trial_start=100, trial_end=109. (Target block 0)
    # Source window: 50 to 90.
    accuracy_data = {
        'subject_id': ['S1'],
        'block_id': [0],
        'accuracy': [0.8],
        'trial_start': [100],
        'trial_end': [109]
    }
    accuracy_df = pd.DataFrame(accuracy_data)
    
    # Write mock files
    mmn_path = os.path.join(temp_data_dir, "preprocessed_epochs.csv")
    accuracy_path = os.path.join(temp_data_dir, "accuracy_blocks.csv")
    
    mmn_df_shifted.to_csv(mmn_path, index=False)
    accuracy_df.to_csv(accuracy_path, index=False)
    
    # Run pipeline
    output_path = os.path.join(temp_data_dir, "interim_lagged_mmns.csv")
    result_df = run_lagged_alignment_pipeline(
        mmn_epochs=mmn_df_shifted,
        accuracy_blocks=accuracy_df,
        output_path=output_path
    )
    
    # Verify schema
    expected_cols = ['subject_id', 'block_id', 'mmn_amplitude', 'source_window_start_trial']
    assert list(result_df.columns) == expected_cols, f"Expected columns {expected_cols}, got {list(result_df.columns)}"
    
    # Verify logic
    # Source window start should be 100 - 50 = 50
    assert result_df['source_window_start_trial'].iloc[0] == 50, "Source window start trial calculation incorrect"
    
    # Verify file exists
    assert os.path.exists(output_path), f"Output file {output_path} not created"
    
    # Verify content matches
    loaded_df = pd.read_csv(output_path)
    pd.testing.assert_frame_equal(result_df, loaded_df)

def test_learning_phase_addition(temp_data_dir):
    """
    Test that add_learning_phase correctly adds the learning_phase column.
    """
    # Create mock lagged data
    lagged_data = {
        'subject_id': ['S1', 'S1', 'S1'],
        'block_id': [0, 1, 2],
        'mmn_amplitude': [0.1, 0.2, 0.3],
        'source_window_start_trial': [50, 60, 70]
    }
    lagged_df = pd.DataFrame(lagged_data)
    
    output_path = os.path.join(temp_data_dir, "interim_lagged_mmns.csv")
    lagged_df.to_csv(output_path, index=False)
    
    # Run function
    result_df = add_learning_phase(output_path=output_path)
    
    # Verify column exists
    assert 'learning_phase' in result_df.columns, "learning_phase column not added"
    
    # Verify values (median block_id is 1. 0 < 1 -> Early, 1 >= 1 -> Late, 2 >= 1 -> Late)
    assert result_df.loc[result_df['block_id'] == 0, 'learning_phase'].iloc[0] == "Early"
    assert result_df.loc[result_df['block_id'] == 1, 'learning_phase'].iloc[0] == "Late"
    assert result_df.loc[result_df['block_id'] == 2, 'learning_phase'].iloc[0] == "Late"

def test_lagged_alignment_empty_source_window(temp_data_dir):
    """
    Test that blocks with no data in source window are dropped.
    """
    # MMN data only for trials 0-9
    mmn_data = {
        'subject_id': ['S1'] * 10,
        'trial_id': list(range(10)),
        'block_id': [0] * 10,
        'mmn_amplitude': np.random.randn(10)
    }
    mmn_df = pd.DataFrame(mmn_data)
    
    # Accuracy block starting at trial 100
    # Source window: 50 to 90. No data exists there.
    accuracy_data = {
        'subject_id': ['S1'],
        'block_id': [0],
        'accuracy': [0.8],
        'trial_start': [100],
        'trial_end': [109]
    }
    accuracy_df = pd.DataFrame(accuracy_data)
    
    output_path = os.path.join(temp_data_dir, "interim_lagged_mmns.csv")
    
    # Should raise or return empty? 
    # Based on implementation: "No aligned data generated... raise ValueError"
    # But in the loop, it logs warning and continues. If all dropped, results empty -> ValueError.
    with pytest.raises(ValueError, match="Lagged alignment produced no results"):
        run_lagged_alignment_pipeline(
            mmn_epochs=mmn_df,
            accuracy_blocks=accuracy_df,
            output_path=output_path
        )