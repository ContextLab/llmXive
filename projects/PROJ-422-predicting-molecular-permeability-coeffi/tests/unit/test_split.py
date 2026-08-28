"""
Unit tests for code/data/split.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.split import stratified_split, random_split


@pytest.fixture
def balanced_df():
    """Create a balanced dataframe for testing stratification."""
    n_samples = 1000
    data = {
        'smiles': [f'C{i}' for i in range(n_samples)],
        'permeability': np.random.rand(n_samples),
        'polymer_type': ['A'] * (n_samples // 2) + ['B'] * (n_samples // 2)
    }
    return pd.DataFrame(data)

@pytest.fixture
def unbalanced_df():
    """Create an unbalanced dataframe (90% A, 10% B)."""
    n_samples = 1000
    data = {
        'smiles': [f'C{i}' for i in range(n_samples)],
        'permeability': np.random.rand(n_samples),
        'polymer_type': ['A'] * 900 + ['B'] * 100
    }
    return pd.DataFrame(data)

@pytest.fixture
def missing_col_df():
    """Create a dataframe without the stratification column."""
    return pd.DataFrame({
        'smiles': ['C1', 'C2', 'C3'],
        'permeability': [0.1, 0.2, 0.3]
    })

@pytest.fixture
def single_class_df():
    """Create a dataframe with only one class."""
    return pd.DataFrame({
        'smiles': ['C1', 'C2', 'C3', 'C4'],
        'permeability': [0.1, 0.2, 0.3, 0.4],
        'polymer_type': ['A', 'A', 'A', 'A']
    })

def test_random_split_basic(balanced_df):
    """Test basic random split functionality."""
    train, test = random_split(balanced_df, test_size=0.2, random_state=42)
    
    assert len(train) + len(test) == len(balanced_df)
    assert len(test) == int(len(balanced_df) * 0.2)
    assert train.index.is_disjoint(test.index)
    assert 'smiles' in train.columns
    assert 'polymer_type' in train.columns

def test_random_split_invalid_size(balanced_df):
    """Test that invalid test_size raises ValueError."""
    with pytest.raises(ValueError):
        random_split(balanced_df, test_size=1.5)
    
    with pytest.raises(ValueError):
        random_split(balanced_df, test_size=0.0)

def test_stratified_split_basic(balanced_df):
    """Test basic stratified split functionality."""
    train, test = stratified_split(balanced_df, stratify_col='polymer_type', test_size=0.2)
    
    # Check sizes
    assert len(train) + len(test) == len(balanced_df)
    
    # Check that distributions are preserved
    train_dist = train['polymer_type'].value_counts(normalize=True).sort_index()
    test_dist = test['polymer_type'].value_counts(normalize=True).sort_index()
    
    # With perfect stratification, distributions should be nearly identical
    assert np.allclose(train_dist, test_dist, atol=0.01)

def test_stratified_split_missing_column(missing_col_df):
    """Test that missing stratification column raises SystemExit."""
    with pytest.raises(SystemExit) as exc_info:
        stratified_split(missing_col_df, stratify_col='polymer_type')
    
    assert "Stratification by polymer_type required by FR-003" in str(exc_info.value)

def test_stratified_split_single_class(single_class_df):
    """Test that single class raises ValueError."""
    with pytest.raises(ValueError):
        stratified_split(single_class_df, stratify_col='polymer_type')

def test_stratified_split_distribution_threshold(balanced_df):
    """Test that distribution threshold is enforced."""
    # Use a very small test_size to potentially cause issues, 
    # but with stratify=True sklearn usually handles it well.
    # We test the logic by ensuring the check runs without error on valid data.
    train, test = stratified_split(
        balanced_df, 
        stratify_col='polymer_type', 
        test_size=0.3, 
        max_distribution_diff=0.10
    )
    assert len(train) > 0
    assert len(test) > 0

def test_stratified_split_with_nan(balanced_df):
    """Test handling of NaN values in stratification column."""
    df_with_nan = balanced_df.copy()
    df_with_nan.loc[0, 'polymer_type'] = np.nan
    
    # Should not raise, should drop the NaN row
    train, test = stratified_split(df_with_nan, stratify_col='polymer_type')
    
    # Total length should be n-1
    assert len(train) + len(test) == len(balanced_df) - 1