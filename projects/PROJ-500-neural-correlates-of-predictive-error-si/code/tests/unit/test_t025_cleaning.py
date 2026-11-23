import os
import sys
import pytest
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.clean import (
    load_interim_lagged_mmns,
    load_accuracy_blocks,
    filter_blocks_by_trial_count,
    handle_nan_values,
    run_cleaning_pipeline
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock data files for T025."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir)
        
        # Create mock interim_lagged_mmns.csv
        # Columns: subject_id, block_id, mmn_amplitude, source_window_start_trial
        mmn_data = {
            'subject_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S3'],
            'block_id': [1, 2, 3, 1, 2, 1],
            'mmn_amplitude': [0.5, np.nan, 0.8, 0.6, 0.7, 0.4], # Block 2 of S1 is NaN
            'source_window_start_trial': [0, 10, 20, 0, 10, 0]
        }
        mmn_df = pd.DataFrame(mmn_data)
        mmn_df.to_csv(data_path / "interim_lagged_mmns.csv", index=False)
        
        # Create mock accuracy_blocks.csv
        # Columns: subject_id, block_id, accuracy, trial_start, trial_end
        # Assuming 10 trials per block, so trial_end - trial_start + 1 = 10
        # We will create a scenario where one block has <10 trials
        acc_data = {
            'subject_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S3'],
            'block_id': [1, 2, 3, 1, 2, 1],
            'accuracy': [0.9, 0.85, 0.95, 0.8, 0.75, 0.9],
            'trial_start': [0, 10, 20, 0, 10, 0],
            'trial_end': [9, 19, 29, 9, 19, 8] # S3 block 1 has trials 0-8 (9 trials) -> Invalid
        }
        acc_df = pd.DataFrame(acc_data)
        acc_df.to_csv(data_path / "accuracy_blocks.csv", index=False)
        
        yield data_path

def test_filter_blocks_by_trial_count(temp_data_dir):
    """Test that blocks with <10 trials are removed."""
    mmn_df = pd.read_csv(temp_data_dir / "interim_lagged_mmns.csv")
    acc_df = pd.read_csv(temp_data_dir / "accuracy_blocks.csv")
    
    filtered_mmn, filtered_acc, removed_count = filter_blocks_by_trial_count(mmn_df, acc_df)
    
    # S3 block 1 should be removed because trial_end (8) - trial_start (0) + 1 = 9 < 10
    assert 'S3' not in filtered_mmn['subject_id'].values or (filtered_mmn['subject_id'] == 'S3').sum() == 0
    assert 3 in filtered_acc['block_id'].values # S1 block 3 is valid
    assert 1 in filtered_acc[filtered_acc['subject_id'] == 'S3']['block_id'].values == False # S3 block 1 removed
    
    # Check that S3 block 1 is gone from both
    assert not filtered_acc[(filtered_acc['subject_id'] == 'S3') & (filtered_acc['block_id'] == 1)].empty == False

def test_handle_nan_values(temp_data_dir):
    """Test that blocks with NaN values are removed."""
    mmn_df = pd.read_csv(temp_data_dir / "interim_lagged_mmns.csv")
    acc_df = pd.read_csv(temp_data_dir / "accuracy_blocks.csv")
    
    # First filter by trial count to ensure we are testing NaN logic
    filtered_mmn, filtered_acc, _ = filter_blocks_by_trial_count(mmn_df, acc_df)
    
    cleaned_mmn, cleaned_acc, nan_removed = handle_nan_values(filtered_mmn, filtered_acc)
    
    # S1 Block 2 has NaN in mmn_amplitude, should be removed
    assert not cleaned_mmn[(cleaned_mmn['subject_id'] == 'S1') & (cleaned_mmn['block_id'] == 2)].empty == False
    assert nan_removed > 0

def test_run_cleaning_pipeline(temp_data_dir):
    """Test the full pipeline execution and output generation."""
    output_dir = temp_data_dir
    
    success = run_cleaning_pipeline(temp_data_dir, output_dir)
    
    assert success is True
    
    # Check output files exist
    assert (output_dir / "filtered_lagged_mmns.csv").exists()
    assert (output_dir / "filtered_accuracy_blocks.csv").exists()
    assert (output_dir / "cleaning_report.json").exists()
    
    # Verify content
    out_mmn = pd.read_csv(output_dir / "filtered_lagged_mmns.csv")
    out_acc = pd.read_csv(output_dir / "filtered_accuracy_blocks.csv")
    
    # Should not contain NaN in mmn_amplitude
    assert out_mmn['mmn_amplitude'].isna().sum() == 0
    
    # Should not contain blocks with <10 trials (S3 block 1)
    s3_blocks = out_acc[out_acc['subject_id'] == 'S3']
    if not s3_blocks.empty:
        # Check trial counts
        for _, row in s3_blocks.iterrows():
            count = row['trial_end'] - row['trial_start'] + 1
            assert count >= 10, f"Block {row['block_id']} has {count} trials"
    
    # Verify report
    with open(output_dir / "cleaning_report.json") as f:
        report = json.load(f)
    
    assert "input_mmn_rows" in report
    assert "output_mmn_rows" in report
    assert report["output_mmn_rows"] < report["input_mmn_rows"] # Some should be removed