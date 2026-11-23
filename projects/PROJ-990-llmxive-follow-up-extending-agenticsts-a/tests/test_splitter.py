import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
import shutil
from pathlib import Path

# Import the functions to test
import sys
sys.path.insert(0, 'code')
from splitter import (
    load_processed_data,
    stratified_split,
    validate_split,
    save_split_data,
    MIN_VALIDATION_SIZE,
    SPLIT_RATIOS
)

@pytest.fixture
def sample_data():
    """Create a sample DataFrame with enough rows to satisfy validation constraints."""
    n_samples = 200  # Ensure validation set >= 20
    data = {
        'trajectory_id': [f'traj_{i}' for i in range(n_samples)],
        'turn': np.random.randint(1, 100, n_samples),
        'move_entropy': np.random.rand(n_samples),
        'win_rate': np.random.rand(n_samples)  # Stratification key
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing file I/O."""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)

def test_load_processed_data_missing_file():
    """Test that load_processed_data raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_processed_data('non_existent_path.csv')

def test_load_processed_data_missing_columns(sample_data, temp_dir):
    """Test that load_processed_data raises ValueError for missing required columns."""
    # Remove required column
    bad_df = sample_data.drop(columns=['move_entropy'])
    filepath = os.path.join(temp_dir, 'bad.csv')
    bad_df.to_csv(filepath, index=False)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        load_processed_data(filepath)

def test_stratified_split_min_validation(sample_data):
    """Test that stratified_split raises ValueError if validation set < 20."""
    # Create a small dataset where validation set would be < 20
    # With 20% split, we need at least 100 samples to get 20 in validation
    small_data = sample_data.head(50) # 50 * 0.2 = 10 < 20
    
    with pytest.raises(ValueError, match="Validation set size.*violates FR-006"):
        stratified_split(small_data)

def test_stratified_split_disjoint(sample_data):
    """Test that the splits are disjoint."""
    train_df, ablation_train_df, validation_df, test_df = stratified_split(sample_data)
    
    all_ids = set(train_df['trajectory_id']) | set(ablation_train_df['trajectory_id']) | \
              set(validation_df['trajectory_id']) | set(test_df['trajectory_id'])
    
    total_count = len(train_df) + len(ablation_train_df) + len(validation_df) + len(test_df)
    
    assert len(all_ids) == total_count, "Splits are not disjoint or missing data"

def test_stratified_split_validation_size(sample_data):
    """Test that validation set meets minimum size requirement."""
    train_df, ablation_train_df, validation_df, test_df = stratified_split(sample_data)
    
    assert len(validation_df) >= MIN_VALIDATION_SIZE, f"Validation set size {len(validation_df)} < {MIN_VALIDATION_SIZE}"

def test_save_split_data(temp_dir, sample_data):
    """Test that save_split_data creates the correct files."""
    train_df, ablation_train_df, validation_df, test_df = stratified_split(sample_data)
    validation_ids = validation_df['trajectory_id'].tolist()
    
    save_split_data(train_df, ablation_train_df, validation_df, test_df, temp_dir, validation_ids)
    
    # Check files exist
    assert os.path.exists(os.path.join(temp_dir, 'train_set.csv'))
    assert os.path.exists(os.path.join(temp_dir, 'ablation_train_set.csv'))
    assert os.path.exists(os.path.join(temp_dir, 'validation_set.csv'))
    assert os.path.exists(os.path.join(temp_dir, 'test_set.csv'))
    assert os.path.exists(os.path.join(temp_dir, 'validation_set_ids.json'))
    
    # Check JSON content
    with open(os.path.join(temp_dir, 'validation_set_ids.json'), 'r') as f:
        loaded_ids = json.load(f)
    assert set(loaded_ids) == set(validation_ids)

def test_validate_split_true(sample_data):
    """Test validate_split returns True for valid splits."""
    train_df, ablation_train_df, validation_df, test_df = stratified_split(sample_data)
    assert validate_split(train_df, ablation_train_df, validation_df, test_df) is True

def test_validate_split_false_overlap(sample_data):
    """Test validate_split returns False if there is overlap."""
    train_df, ablation_train_df, validation_df, test_df = stratified_split(sample_data)
    
    # Introduce overlap manually
    overlap_id = train_df.iloc[0]['trajectory_id']
    validation_df = pd.concat([validation_df, pd.DataFrame([{'trajectory_id': overlap_id}])])
    
    assert validate_split(train_df, ablation_train_df, validation_df, test_df) is False