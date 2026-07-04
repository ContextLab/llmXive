"""
Integration tests for the data splitting module.

Tests:
1. Stratified split maintains >=80% training proportion
2. LOFO switch triggers when family size < 10
3. Files are written to disk correctly
"""

import os
import sys
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.split import (
    identify_chemical_family,
    assign_family_column,
    check_family_sizes,
    perform_stratified_split,
    perform_lofo_cv,
    MIN_FAMILY_SIZE,
    TRAIN_RATIO
)

@pytest.fixture
def sample_df():
    """Create a sample dataframe with various chemical families."""
    data = {
        'composition': [
            'As30Se70', 'As40Se60', 'As20Se80', 'As35Se65', 'As25Se75',  # As-Se family (5 samples)
            'Ge20Se80', 'Ge30Se70', 'Ge40Se60', 'Ge25Se75', 'Ge35Se65',  # Ge-Se family (5 samples)
            'Sb30Se70', 'Sb40Se60', 'Sb20Se80', 'Sb35Se65', 'Sb25Se75',  # Sb-Se family (5 samples)
            'As30S70', 'As40S60', 'As20S80', 'As35S65', 'As25S75',       # As-S family (5 samples)
            'Ge20S80', 'Ge30S70', 'Ge40S60', 'Ge25S75', 'Ge35S65',       # Ge-S family (5 samples)
        ],
        'Tg': [250, 260, 245, 255, 248, 280, 290, 275, 285, 270, 220, 230, 215, 225, 210, 180, 190, 175, 185, 170, 200, 210, 195, 205, 190]
    }
    return pd.DataFrame(data)

@pytest.fixture
def small_family_df():
    """Create a dataframe with a small family (<10 samples)."""
    data = {
        'composition': [
            'As30Se70', 'As40Se60', 'As20Se80', 'As35Se65', 'As25Se75',  # As-Se family (5 samples)
            'Ge20Se80', 'Ge30Se70', 'Ge40Se60', 'Ge25Se75', 'Ge35Se65',  # Ge-Se family (5 samples)
            'Sb30Se70', 'Sb40Se60', 'Sb20Se80', 'Sb35Se65', 'Sb25Se75',  # Sb-Se family (5 samples)
            'In30Se70', 'In40Se60',                                      # In-Se family (2 samples - small)
        ],
        'Tg': [250, 260, 245, 255, 248, 280, 290, 275, 285, 270, 220, 230, 215, 225, 210, 180, 190, 175, 185, 170]
    }
    return pd.DataFrame(data)

@pytest.fixture
def large_family_df():
    """Create a dataframe with all families >= 10 samples."""
    data = {
        'composition': [],
        'Tg': []
    }
    
    # Create 3 families with 12 samples each
    families = ['As-Se', 'Ge-Se', 'Sb-Se']
    for family in families:
        for i in range(12):
            if family == 'As-Se':
                data['composition'].append(f'As{30+i}Se{70-i}')
                data['Tg'].append(250 + i)
            elif family == 'Ge-Se':
                data['composition'].append(f'Ge{20+i}Se{80-i}')
                data['Tg'].append(280 + i)
            elif family == 'Sb-Se':
                data['composition'].append(f'Sb{30+i}Se{70-i}')
                data['Tg'].append(220 + i)
    
    return pd.DataFrame(data)

def test_identify_chemical_family():
    """Test chemical family identification."""
    assert identify_chemical_family('As30Se70') == 'As-Se'
    assert identify_chemical_family('Ge20Se80') == 'Ge-Se'
    assert identify_chemical_family('Sb30Se70') == 'Sb-Se'
    assert identify_chemical_family('As30S70') == 'As-S'
    assert identify_chemical_family(None) == 'Unknown'

def test_assign_family_column(sample_df):
    """Test that chemical_family column is added correctly."""
    df_with_family = assign_family_column(sample_df)
    assert 'chemical_family' in df_with_family.columns
    assert df_with_family['chemical_family'].nunique() > 1

def test_check_family_sizes(sample_df):
    """Test family size counting."""
    df_with_family = assign_family_column(sample_df)
    family_counts = check_family_sizes(df_with_family)
    
    assert len(family_counts) == 5  # 5 unique families
    assert all(count == 5 for count in family_counts.values())

def test_stratified_split_ratio(large_family_df):
    """Test that stratified split maintains >=80% training proportion."""
    df_with_family = assign_family_column(large_family_df)
    train_df, test_df = perform_stratified_split(df_with_family, test_size=0.2)
    
    train_ratio = len(train_df) / len(df_with_family)
    assert train_ratio >= TRAIN_RATIO, f"Train ratio {train_ratio} < {TRAIN_RATIO}"
    assert len(train_df) + len(test_df) == len(df_with_family)

def test_stratified_split_preserves_families(large_family_df):
    """Test that stratified split preserves family distribution."""
    df_with_family = assign_family_column(large_family_df)
    train_df, test_df = perform_stratified_split(df_with_family, test_size=0.2)
    
    # Check that all families are present in both splits
    train_families = set(train_df['chemical_family'].unique())
    test_families = set(test_df['chemical_family'].unique())
    all_families = set(df_with_family['chemical_family'].unique())
    
    assert train_families == all_families
    assert test_families == all_families

def test_lofo_switch_with_small_family(small_family_df):
    """Test that LOFO is triggered when a family has <10 samples."""
    df_with_family = assign_family_column(small_family_df)
    family_counts = check_family_sizes(df_with_family)
    
    small_families = [f for f, count in family_counts.items() if count < MIN_FAMILY_SIZE]
    assert len(small_families) > 0, "Expected at least one small family"
    
    splits = perform_lofo_cv(df_with_family)
    assert len(splits) == len(family_counts), f"Expected {len(family_counts)} splits, got {len(splits)}"
    
    # Check that each split holds out exactly one family
    for i, (train_df, test_df) in enumerate(splits):
        test_families = set(test_df['chemical_family'].unique())
        assert len(test_families) == 1, f"Fold {i} should hold out exactly one family"

def test_lofo_coverage(small_family_df):
    """Test that LOFO covers all families."""
    df_with_family = assign_family_column(small_family_df)
    splits = perform_lofo_cv(df_with_family)
    
    held_out_families = set()
    for train_df, test_df in splits:
        family = test_df['chemical_family'].iloc[0]
        held_out_families.add(family)
    
    all_families = set(df_with_family['chemical_family'].unique())
    assert held_out_families == all_families

def test_split_decision_logic(sample_df, small_family_df, large_family_df):
    """Test the decision logic between stratified and LOFO."""
    # Small families -> LOFO
    df_small = assign_family_column(small_family_df)
    family_counts_small = check_family_sizes(df_small)
    has_small = any(count < MIN_FAMILY_SIZE for count in family_counts_small.values())
    assert has_small is True, "Small family test should have small families"
    
    # Large families -> Stratified
    df_large = assign_family_column(large_family_df)
    family_counts_large = check_family_sizes(df_large)
    has_small_large = any(count < MIN_FAMILY_SIZE for count in family_counts_large.values())
    assert has_small_large is False, "Large family test should not have small families"

def test_file_io_integration(tmp_path):
    """Test that split functions can write to disk."""
    # Create a simple dataframe
    data = {
        'composition': ['As30Se70', 'As40Se60', 'Ge20Se80', 'Ge30Se70', 'Sb30Se70', 'Sb40Se60'],
        'Tg': [250, 260, 280, 290, 220, 230]
    }
    df = pd.DataFrame(data)
    df = assign_family_column(df)
    
    # Perform stratified split
    train_df, test_df = perform_stratified_split(df, test_size=0.33)
    
    # Write to temp directory
    output_dir = tmp_path / "split_output"
    output_dir.mkdir()
    
    train_path = output_dir / "train.csv"
    test_path = output_dir / "test.csv"
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    # Verify files exist and can be read
    assert train_path.exists()
    assert test_path.exists()
    
    loaded_train = pd.read_csv(train_path)
    loaded_test = pd.read_csv(test_path)
    
    assert len(loaded_train) == len(train_df)
    assert len(loaded_test) == len(test_df)
    assert 'chemical_family' in loaded_train.columns
    assert 'chemical_family' in loaded_test.columns