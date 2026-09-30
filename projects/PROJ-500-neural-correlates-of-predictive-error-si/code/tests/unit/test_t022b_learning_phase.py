import os
import sys
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

from src.data.align import add_learning_phase, run_learning_phase_pipeline
from src.utils.config import get_accuracy_block_size

def test_add_learning_phase_basic():
    """Test basic functionality of add_learning_phase."""
    # Create mock data with block_id
    df = pd.DataFrame({
        'subject_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S2'],
        'block_id': [0, 1, 2, 0, 1, 2],
        'mmn_amplitude': [1.0, 1.5, 2.0, 1.1, 1.6, 2.1]
    })
    
    result = add_learning_phase(df)
    
    assert 'learning_phase' in result.columns
    assert result['learning_phase'].nunique() == 2
    assert set(result['learning_phase'].unique()).issubset({'Early', 'Late'})
    
    # Check that blocks 0,1 are Early and 2 is Late (assuming 3 blocks total, mid=1)
    # With 3 blocks (0,1,2), mid_point = 3//2 = 1. So 0 < 1 (Early), 1 >= 1 (Late), 2 >= 1 (Late)
    # Wait, logic: relative_block < mid_point -> Early
    # relative_block 0 < 1 -> Early
    # relative_block 1 >= 1 -> Late
    # relative_block 2 >= 1 -> Late
    # So we expect 1 Early, 2 Late
    assert (result['learning_phase'] == 'Early').sum() == 1
    assert (result['learning_phase'] == 'Late').sum() == 2

def test_add_learning_phase_from_trial_start():
    """Test add_learning_phase using trial_start instead of block_id."""
    block_size = get_accuracy_block_size()
    
    # Create mock data with trial_start
    df = pd.DataFrame({
        'subject_id': ['S1', 'S1', 'S1'],
        'trial_start': [0, 10, 20],  # Assuming block_size=10
        'mmn_amplitude': [1.0, 1.5, 2.0]
    })
    
    result = add_learning_phase(df)
    
    assert 'learning_phase' in result.columns
    assert result['learning_phase'].nunique() == 2

def test_add_learning_phase_invalid_input():
    """Test that add_learning_phase raises error for invalid input."""
    df = pd.DataFrame({
        'subject_id': ['S1'],
        'mmn_amplitude': [1.0]
    })
    
    with pytest.raises(ValueError):
        add_learning_phase(df)

def test_add_learning_phase_single_block():
    """Test behavior when only one block exists."""
    df = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [0],
        'mmn_amplitude': [1.0]
    })
    
    # With only one block, mid_point = 1//2 = 0. relative_block 0 < 0 is False.
    # So it should be Late.
    result = add_learning_phase(df)
    
    assert 'learning_phase' in result.columns
    assert result['learning_phase'].iloc[0] == 'Late'

def test_run_learning_phase_pipeline_integration(tmp_path):
    """Integration test for run_learning_phase_pipeline."""
    # Setup temporary data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create mock interim_lagged_mmns.csv
    mock_data = pd.DataFrame({
        'subject_id': ['S1', 'S1', 'S1', 'S1', 'S1', 'S1'],
        'block_id': [0, 1, 2, 3, 4, 5],
        'mmn_amplitude': [1.0, 1.2, 1.4, 1.6, 1.8, 2.0],
        'source_window_start_trial': [0, 10, 20, 30, 40, 50]
    })
    
    input_file = data_dir / "interim_lagged_mmns.csv"
    mock_data.to_csv(input_file, index=False)
    
    # Run pipeline
    run_learning_phase_pipeline(str(data_dir))
    
    # Verify output
    output_df = pd.read_csv(input_file)
    
    assert 'learning_phase' in output_df.columns
    assert output_df['learning_phase'].nunique() == 2
    assert set(output_df['learning_phase'].unique()).issubset({'Early', 'Late'})
    
    # Check distribution (6 blocks: 0,1,2,3,4,5. mid=6//2=3. 0,1,2 < 3 (Early), 3,4,5 >= 3 (Late))
    assert (output_df['learning_phase'] == 'Early').sum() == 3
    assert (output_df['learning_phase'] == 'Late').sum() == 3

def test_learning_phase_column_persistence(tmp_path):
    """Test that if learning_phase already exists, it is not regenerated."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create mock data with existing learning_phase
    mock_data = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [0],
        'mmn_amplitude': [1.0],
        'learning_phase': ['Early']
    })
    
    input_file = data_dir / "interim_lagged_mmns.csv"
    mock_data.to_csv(input_file, index=False)
    
    # Run pipeline
    run_learning_phase_pipeline(str(data_dir))
    
    # Verify output is unchanged (still has 'Early')
    output_df = pd.read_csv(input_file)
    assert output_df['learning_phase'].iloc[0] == 'Early'
    assert len(output_df) == 1
