"""
Unit test for CV split logic.

This test verifies that GroupKFold splits the data correctly by alloy system,
ensuring that no alloy system appears in both training and testing sets simultaneously.
This is critical for the 'held-out alloy system' evaluation strategy (SC-001).
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import GroupKFold
import sys
from pathlib import Path

# Ensure the project code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

def test_group_kfold_split():
    """
    Test that GroupKFold splits data correctly by alloy system.
    Ensures that entire groups (alloy systems) are held out as test sets.
    """
    # Create mock data representing different alloy systems
    # Using fixed seed for reproducibility in tests
    rng = np.random.default_rng(42)
    
    data = pd.DataFrame({
        'feature': rng.random(10),
        'target': rng.random(10),
        'alloy_system': ['BCC_Fe'] * 5 + ['FCC_Cu'] * 5
    })

    groups = data['alloy_system']

    # Initialize GroupKFold with 2 splits (since we have 2 unique groups)
    gkf = GroupKFold(n_splits=2)
    splits = list(gkf.split(data, groups=groups))

    # Verify we got exactly 2 splits
    assert len(splits) == 2, f"Expected 2 splits, got {len(splits)}"

    # Verify that each split has distinct groups in train and test
    for i, (train_idx, test_idx) in enumerate(splits):
        train_groups = set(groups.iloc[train_idx].unique())
        test_groups = set(groups.iloc[test_idx].unique())
        
        # Ensure no overlap between train and test groups
        intersection = train_groups & test_groups
        assert len(intersection) == 0, (
            f"Split {i}: Groups overlap between train and test: {intersection}. "
            "Alloy systems must be mutually exclusive in train/test splits."
        )
        
        # Verify that the union of train and test groups contains all groups
        all_groups = set(groups.unique())
        assert train_groups | test_groups == all_groups, (
            f"Split {i}: Missing groups in split. Expected {all_groups}, got {train_groups | test_groups}"
        )

def test_single_group_handling():
    """
    Test that GroupKFold handles a dataset with only one group correctly.
    In this case, it should produce a single split where the test set is empty
    or raise an error depending on sklearn version, but we expect it to handle gracefully.
    """
    data = pd.DataFrame({
        'feature': np.random.rand(5),
        'target': np.random.rand(5),
        'alloy_system': ['BCC_Fe'] * 5
    })

    groups = data['alloy_system']
    
    # With n_splits=1, we expect one split
    gkf = GroupKFold(n_splits=1)
    splits = list(gkf.split(data, groups=groups))
    
    assert len(splits) == 1, "Expected 1 split for single group dataset"
    
    train_idx, test_idx = splits[0]
    # All data should be in training, test should be empty or valid
    assert len(train_idx) == 5, "All samples should be in training set"
    # test_idx might be empty or contain samples depending on implementation,
    # but the key is that the group logic holds.

def test_multiple_groups_cross_validation():
    """
    Test GroupKFold with more groups than splits to ensure proper distribution.
    """
    rng = np.random.default_rng(123)
    n_samples = 20
    n_groups = 4
    samples_per_group = n_samples // n_groups
    
    alloy_systems = [f"System_{i}" for i in range(n_groups)]
    data = pd.DataFrame({
        'feature': rng.random(n_samples),
        'target': rng.random(n_samples),
        'alloy_system': [alloy_systems[i // samples_per_group] for i in range(n_samples)]
    })

    groups = data['alloy_system']
    n_splits = 2
    
    gkf = GroupKFold(n_splits=n_splits)
    splits = list(gkf.split(data, groups=groups))

    assert len(splits) == n_splits, f"Expected {n_splits} splits, got {len(splits)}"

    for i, (train_idx, test_idx) in enumerate(splits):
        train_groups = set(groups.iloc[train_idx].unique())
        test_groups = set(groups.iloc[test_idx].unique())
        
        # Verify no overlap
        assert len(train_groups & test_groups) == 0, (
            f"Split {i}: Group overlap detected between train and test."
        )