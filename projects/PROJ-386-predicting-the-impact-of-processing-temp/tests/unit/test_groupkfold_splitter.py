import pytest
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

# Import the function to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.preprocessing import create_group_kfold_splitter, extract_alloy_series

def test_create_group_kfold_splitter_initialization():
    """Test that the splitter is correctly instantiated."""
    groups = np.array([1, 1, 2, 2, 3, 3])
    splitter = create_group_kfold_splitter(groups, n_splits=3)
    
    assert isinstance(splitter, GroupKFold)
    assert splitter.n_splits == 3

def test_create_group_kfold_splitter_empty_groups():
    """Test that empty groups raise an error."""
    groups = np.array([])
    with pytest.raises(ValueError, match="Groups array is empty"):
        create_group_kfold_splitter(groups)

def test_create_group_kfold_splitter_no_overlap():
    """Test that the splitter ensures no group appears in both train and test."""
    # Create a small dataset with known groups
    groups = np.array([1, 1, 2, 2, 3, 3, 4, 4])
    splitter = create_group_kfold_splitter(groups, n_splits=4)
    
    # Iterate through splits to verify non-overlap
    for train_idx, test_idx in splitter.split(groups, groups=groups):
        train_groups = groups[train_idx]
        test_groups = groups[test_idx]
        
        # Check intersection
        overlap = set(train_groups) & set(test_groups)
        assert len(overlap) == 0, f"Overlap found in groups: {overlap}"

def test_extract_alloy_series_fallback():
    """Test extraction of alloy series with standard column names."""
    df = pd.DataFrame({
        'Alloy_Series': [1, 1, 2, 2],
        'Temp': [100, 100, 100, 100],
        'Grain_Size': [10, 12, 11, 13]
    })
    groups = extract_alloy_series(df)
    assert np.array_equal(groups, np.array([1, 1, 2, 2]))

def test_extract_alloy_series_missing():
    """Test that missing alloy series raises an error."""
    df = pd.DataFrame({
        'Temp': [100, 100],
        'Grain_Size': [10, 12]
    })
    with pytest.raises(ValueError, match="Alloy Series column not found"):
        extract_alloy_series(df)