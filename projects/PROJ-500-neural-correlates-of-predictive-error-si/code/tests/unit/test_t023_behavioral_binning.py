"""
Unit tests for T023: Behavioral Binning Logic.

Tests the calculation of accuracy over 10-trial blocks.
"""

import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.align import (
    calculate_block_accuracy,
    bin_behavioral_data,
    DEFAULT_BLOCK_SIZE
)


def create_mock_epochs_data():
    """
    Create a mock DataFrame representing trial-level data.
    Columns: subject_id, trial_id, response_correct
    """
    data = []
    # Subject 1: 30 trials, 100% correct
    for i in range(30):
        data.append({'subject_id': 'S01', 'trial_id': i, 'response_correct': 1})
    
    # Subject 2: 20 trials, alternating correct/incorrect (50%)
    for i in range(20):
        data.append({'subject_id': 'S02', 'trial_id': i, 'response_correct': i % 2})
    
    # Subject 3: 15 trials, mixed
    for i in range(15):
        # 8 correct, 7 incorrect
        correct = 1 if i < 8 else 0
        data.append({'subject_id': 'S03', 'trial_id': i, 'response_correct': correct})
    
    return pd.DataFrame(data)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def temp_data_dir_non_stationary():
    """Create a temporary directory with non-stationary data (learning effect)."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


def test_calculate_block_accuracy():
    """Test accuracy calculation for a single subject."""
    df = create_mock_epochs_data()
    
    # Test Subject 1 (30 trials, 100% correct)
    result = calculate_block_accuracy(df, 'S01', block_size=10)
    
    assert len(result) == 3, "Should have 3 blocks of 10 trials."
    assert all(result['accuracy'] == 1.0), "All blocks should be 100% accurate."
    assert result['trial_start'].tolist() == [0, 10, 20], "Trial starts should be 0, 10, 20."
    assert result['trial_end'].tolist() == [9, 19, 29], "Trial ends should be 9, 19, 29."
    
    # Test Subject 2 (20 trials, 50% correct)
    result = calculate_block_accuracy(df, 'S02', block_size=10)
    
    assert len(result) == 2, "Should have 2 blocks."
    # Block 0: trials 0-9 (0,1,0,1,0,1,0,1,0,1) -> 5 correct -> 0.5
    # Block 1: trials 10-19 (0,1,0,1,0,1,0,1,0,1) -> 5 correct -> 0.5
    assert result['accuracy'].tolist() == [0.5, 0.5], "Both blocks should be 50% accurate."


def test_check_stationarity_stable():
    """Test with stable performance (no learning effect)."""
    # Create data where accuracy is constant
    data = []
    for i in range(100):
        data.append({'subject_id': 'S01', 'trial_id': i, 'response_correct': 1 if i % 2 == 0 else 0})
    
    df = pd.DataFrame(data)
    result = bin_behavioral_data(df, block_size=10)
    
    # All blocks should have 50% accuracy
    assert all(result['accuracy'] == 0.5), "Stable data should result in constant accuracy blocks."


def test_check_stationarity_trending():
    """Test with trending performance (learning effect)."""
    data = []
    # First 50 trials: 0% correct
    for i in range(50):
        data.append({'subject_id': 'S01', 'trial_id': i, 'response_correct': 0})
    # Next 50 trials: 100% correct
    for i in range(50, 100):
        data.append({'subject_id': 'S01', 'trial_id': i, 'response_correct': 1})
    
    df = pd.DataFrame(data)
    result = bin_behavioral_data(df, block_size=10)
    
    # First 5 blocks should be 0, next 5 blocks should be 1
    assert result['accuracy'].iloc[0] == 0.0
    assert result['accuracy'].iloc[4] == 0.0
    assert result['accuracy'].iloc[5] == 1.0
    assert result['accuracy'].iloc[9] == 1.0


def test_bin_behavioral_data_success():
    """Test full binning pipeline on mock data."""
    df = create_mock_epochs_data()
    result = bin_behavioral_data(df, block_size=10)
    
    assert 'subject_id' in result.columns
    assert 'block_id' in result.columns
    assert 'accuracy' in result.columns
    assert 'trial_start' in result.columns
    assert 'trial_end' in result.columns
    
    # S01: 30 trials -> 3 blocks
    # S02: 20 trials -> 2 blocks
    # S03: 15 trials -> 1 full block (0-9), 1 partial block (10-14)
    # Total blocks = 3 + 2 + 2 = 7
    assert len(result) == 7, f"Expected 7 blocks, got {len(result)}"
    
    # Check S03 partial block
    s03_blocks = result[result['subject_id'] == 'S03']
    assert len(s03_blocks) == 2
    # Last block should have 5 trials (10-14)
    assert s03_blocks.iloc[1]['trial_end'] - s03_blocks.iloc[1]['trial_start'] + 1 == 5
    # Accuracy for last block: trials 10-14 are all 0 (incorrect) -> 0.0
    assert s03_blocks.iloc[1]['accuracy'] == 0.0


def test_bin_behavioral_data_small_blocks():
    """Test binning with very small block sizes."""
    data = []
    for i in range(5):
        data.append({'subject_id': 'S01', 'trial_id': i, 'response_correct': 1})
    
    df = pd.DataFrame(data)
    result = bin_behavioral_data(df, block_size=2)
    
    # 5 trials, block size 2 -> 2 full blocks (0-1, 2-3), 1 partial (4)
    assert len(result) == 3
    assert result.iloc[0]['trial_end'] == 1
    assert result.iloc[1]['trial_end'] == 3
    assert result.iloc[2]['trial_end'] == 4


def test_bin_behavioral_data_non_stationary(temp_data_dir_non_stationary):
    """Test handling of non-stationary data (learning curves)."""
    # This is effectively the same as test_check_stationarity_trending
    # but verifies the function handles it gracefully without crashing
    data = []
    for i in range(100):
        # Linear increase in accuracy
        prob_correct = i / 100.0
        correct = 1 if np.random.rand() < prob_correct else 0
        data.append({'subject_id': 'S01', 'trial_id': i, 'response_correct': correct})
    
    df = pd.DataFrame(data)
    result = bin_behavioral_data(df, block_size=10)
    
    # Should not crash, should produce 10 blocks
    assert len(result) == 10
    # Accuracy should generally increase (not strictly guaranteed due to randomness, but trend should exist)
    # We just check it runs without error here.


def test_run_behavioral_binning_pipeline(temp_data_dir):
    """
    Test the full pipeline execution writing to disk.
    Note: This test requires the 'run_lagged_alignment_pipeline' to be called,
    but since we are only testing T023 (binning), we test the binning function
    directly and verify file creation.
    """
    from src.data.align import bin_behavioral_data
    
    df = create_mock_epochs_data()
    output_path = temp_data_dir / "accuracy_blocks.csv"
    
    result_df = bin_behavioral_data(df, block_size=10)
    result_df.to_csv(output_path, index=False)
    
    assert output_path.exists(), "Output file should be created."
    
    # Reload and verify
    loaded = pd.read_csv(output_path)
    assert len(loaded) == 7
    assert 'accuracy' in loaded.columns