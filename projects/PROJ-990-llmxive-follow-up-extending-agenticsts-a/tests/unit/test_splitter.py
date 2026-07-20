"""
Unit tests for the splitter module.
"""
import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
import tempfile
import shutil

# Import the module under test
from splitter import (
    load_processed_data,
    stratified_split,
    train_test_split,
    save_split_data,
    validate_split,
    DEFAULT_TRAIN_RATIO,
    STRATIFY_COLUMN
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        'trajectory_id': range(100),
        'turn': np.random.randint(0, 50, 100),
        'utility_score': np.random.choice([0, 1, 2, 3], 100),
        'entropy': np.random.rand(100),
        'health': np.random.randint(10, 100, 100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

def test_load_processed_data(sample_data, temp_dir):
    """Test loading processed data from CSV."""
    test_file = os.path.join(temp_dir, "test_data.csv")
    sample_data.to_csv(test_file, index=False)
    
    loaded_df = load_processed_data(test_file)
    assert len(loaded_df) == len(sample_data)
    assert list(loaded_df.columns) == list(sample_data.columns)

def test_load_processed_data_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_processed_data("nonexistent/path.csv")

def test_stratified_split_stratification(sample_data):
    """Test that stratified split maintains distribution."""
    train_df, holdout_df = stratified_split(sample_data, train_ratio=0.8)
    
    # Check sizes
    assert len(train_df) + len(holdout_df) == len(sample_data)
    assert len(train_df) == int(len(sample_data) * 0.8)
    assert len(holdout_df) == int(len(sample_data) * 0.2)
    
    # Check no overlap
    train_ids = set(train_df['trajectory_id'])
    holdout_ids = set(holdout_df['trajectory_id'])
    assert len(train_ids.intersection(holdout_ids)) == 0

def test_stratified_split_missing_column(sample_data):
    """Test split when stratification column is missing."""
    # Remove the stratification column
    data_no_strat = sample_data.drop(columns=[STRATIFY_COLUMN])
    
    # Should fall back to random split without error
    train_df, holdout_df = stratified_split(data_no_strat)
    assert len(train_df) + len(holdout_df) == len(data_no_strat)

def test_train_test_split_alias(sample_data):
    """Test that train_test_split is an alias for stratified_split."""
    train1, holdout1 = stratified_split(sample_data)
    train2, holdout2 = train_test_split(sample_data)
    
    # Results should be identical (same random state)
    assert len(train1) == len(train2)
    assert len(holdout1) == len(holdout2)

def test_save_split_data(temp_dir, sample_data):
    """Test saving split data to CSV files."""
    train_df = sample_data.iloc[:80]
    holdout_df = sample_data.iloc[80:]
    
    train_path = os.path.join(temp_dir, "train.csv")
    holdout_path = os.path.join(temp_dir, "holdout.csv")
    
    save_split_data(train_df, holdout_df, train_path, holdout_path)
    
    assert os.path.exists(train_path)
    assert os.path.exists(holdout_path)
    
    loaded_train = pd.read_csv(train_path)
    loaded_holdout = pd.read_csv(holdout_path)
    
    assert len(loaded_train) == 80
    assert len(loaded_holdout) == 20

def test_validate_split(sample_data):
    """Test split validation."""
    train_df, holdout_df = stratified_split(sample_data)
    validation_result = validate_split(train_df, holdout_df, sample_data)
    
    assert validation_result['total_original_rows'] == len(sample_data)
    assert validation_result['count_match'] is True
    assert validation_result['no_overlap'] is True
    assert 'stratification_maintained' in validation_result

def test_validate_split_with_overlap():
    """Test validation detects overlap."""
    df = pd.DataFrame({'id': [1, 2, 3, 4], 'value': [10, 20, 30, 40]})
    train_df = df.iloc[:3]
    holdout_df = df.iloc[2:]  # Overlap on index 2
    
    validation_result = validate_split(train_df, holdout_df, df)
    assert validation_result['no_overlap'] is False

def test_stratified_split_small_strata(sample_data):
    """Test split with small strata falls back to random."""
    # Create data with a strata that has only 1 sample
    small_data = sample_data.copy()
    small_data.loc[0, STRATIFY_COLUMN] = 999  # Unique value with count 1
    
    # Should not raise, should fall back to random split
    train_df, holdout_df = stratified_split(small_data)
    assert len(train_df) + len(holdout_df) == len(small_data)

def test_random_state_reproducibility(sample_data):
    """Test that same random state produces same split."""
    train1, holdout1 = stratified_split(sample_data, random_state=42)
    train2, holdout2 = stratified_split(sample_data, random_state=42)
    
    assert train1.equals(train2)
    assert holdout1.equals(holdout2)