"""
Unit tests for T027a: train_split.py
"""
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the functions to test
# We assume the module is named train_split based on the artifact path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from train_split import perform_split, save_split_config, load_features

def test_perform_split_stratified():
    """Test that stratified split works correctly when multiple classes exist."""
    # Create a dummy dataframe
    data = {
        'feature1': [1, 2, 3, 4, 5, 6],
        'primary_dimension': [0, 1, 0, 1, 0, 1] # Balanced
    }
    df = pd.DataFrame(data)
    
    train_idx, test_idx = perform_split(df, test_size=0.5, random_state=42)
    
    # Check lengths
    assert len(train_idx) == 3
    assert len(test_idx) == 3
    
    # Check that stratification was respected (roughly)
    # In a perfect 50/50 split of 3 zeros and 3 ones, we should get 1.5 of each? 
    # Actually, with 6 samples and 50% test, we need 3 train, 3 test.
    # Stratify ensures the proportion in train/test matches the original.
    # Original: 50% dim 0, 50% dim 1.
    # Train should have roughly 50% dim 0, 50% dim 1.
    
    train_dims = df.loc[train_idx, 'primary_dimension']
    test_dims = df.loc[test_idx, 'primary_dimension']
    
    assert train_dims.value_counts().to_dict() == {0: 1, 1: 2} or train_dims.value_counts().to_dict() == {0: 2, 1: 1} # Depends on random_state
    # The key is that it doesn't crash and splits by index.

def test_perform_split_no_stratify_single_class():
    """Test split when only one class exists."""
    data = {
        'feature1': [1, 2, 3, 4, 5, 6],
        'primary_dimension': [0, 0, 0, 0, 0, 0]
    }
    df = pd.DataFrame(data)
    
    # Should not raise an error, just warn (handled by logging in real run)
    train_idx, test_idx = perform_split(df, test_size=0.5, random_state=42)
    
    assert len(train_idx) == 3
    assert len(test_idx) == 3

def test_perform_split_missing_column():
    """Test split when primary_dimension column is missing."""
    data = {
        'feature1': [1, 2, 3, 4, 5, 6]
    }
    df = pd.DataFrame(data)
    
    train_idx, test_idx = perform_split(df, test_size=0.5, random_state=42)
    
    assert len(train_idx) == 3
    assert len(test_idx) == 3

def test_save_split_config(tmp_path):
    """Test saving split configuration."""
    train_indices = [0, 1, 2]
    test_indices = [3, 4, 5]
    output_file = tmp_path / "split_config.json"
    
    save_split_config(train_indices, test_indices, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        config = json.load(f)
    
    assert config['train_indices'] == train_indices
    assert config['test_indices'] == test_indices
    assert config['test_size'] == 0.2
    assert config['random_state'] == 42
    assert config['total_samples'] == 6
    assert config['train_count'] == 3
    assert config['test_count'] == 3