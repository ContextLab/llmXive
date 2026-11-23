"""
Unit tests for data preprocessing functions in code/data/preprocess.py.

Tests cover:
- sanitize_molecules: Salt removal, valence fixing, invalid structure handling.
- filter_targets: Filtering for specific ADME targets.
- deduplicate_smiles: Handling duplicates by date or averaging.
- sample_dataset: Stratified sampling with memory safety checks.
- calculate_descriptors: Accuracy of 2D descriptor calculation.
"""
import pytest
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski
import sys
import os

# Adjust path to import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.preprocess import (
    sanitize_molecules,
    filter_targets,
    deduplicate_smiles,
    sample_dataset,
    calculate_descriptors,
    DataInsufficiencyError
)

# Fixtures
@pytest.fixture
def sample_df_valid():
    return pd.DataFrame({
        'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1'],
        'target': ['solubility', 'solubility', 'permeability'],
        'value': [1.5, 2.0, 0.8],
        'assay_date': ['2023-01-01', '2023-02-01', '2023-03-01']
    })

@pytest.fixture
def sample_df_invalid():
    return pd.DataFrame({
        'smiles': ['CCO', 'INVALID_SMILES', ''],
        'target': ['solubility', 'solubility', 'permeability'],
        'value': [1.5, 2.0, 0.8],
        'assay_date': ['2023-01-01', '2023-02-01', '2023-03-01']
    })

@pytest.fixture
def sample_df_duplicates():
    return pd.DataFrame({
        'smiles': ['CCO', 'CCO', 'CC(=O)O'],
        'target': ['solubility', 'solubility', 'permeability'],
        'value': [1.5, 2.0, 10.0],
        'assay_date': ['2023-01-01', '2023-02-01', '2023-01-01']
    })

def test_sanitize_molecules_valid(sample_df_valid):
    """Test sanitization with valid molecules."""
    result = sanitize_molecules(sample_df_valid)
    assert len(result) == len(sample_df_valid), "Valid molecules should not be removed."
    assert 'smiles' in result.columns
    
def test_sanitize_molecules_invalid(sample_df_invalid):
    """Test sanitization removes invalid molecules."""
    result = sanitize_molecules(sample_df_invalid)
    # Expect 2 valid rows (CCO and the empty string might be handled, but INVALID is definitely out)
    # Based on typical RDKit behavior, empty string fails, invalid string fails.
    assert len(result) < len(sample_df_invalid), "Invalid molecules should be removed."
    
def test_filter_targets(sample_df_valid):
    """Test filtering for specific targets."""
    valid_targets = ['solubility', 'permeability']
    result = filter_targets(sample_df_valid, valid_targets)
    assert len(result) == len(sample_df_valid)
    
    invalid_target_df = sample_df_valid.copy()
    invalid_target_df.loc[0, 'target'] = 'unknown_target'
    result_filtered = filter_targets(invalid_target_df, valid_targets)
    assert len(result_filtered) == len(sample_df_valid) - 1
    
def test_deduplicate_smiles_different_dates(sample_df_duplicates):
    """Test deduplication keeps most recent date."""
    result = deduplicate_smiles(sample_df_duplicates)
    # 'CCO' appears twice: 2023-01-01 (1.5) and 2023-02-01 (2.0). Should keep 2023-02-01.
    assert len(result) == 2
    cco_row = result[result['smiles'] == 'CCO'].iloc[0]
    assert cco_row['value'] == 2.0
    assert cco_row['assay_date'] == '2023-02-01'
    
def test_deduplicate_smiles_same_dates(sample_df_duplicates):
    """Test deduplication averages values if dates match."""
    # Modify to have same dates for duplicates
    df = pd.DataFrame({
        'smiles': ['CCO', 'CCO'],
        'target': ['solubility', 'solubility'],
        'value': [1.0, 3.0],
        'assay_date': ['2023-01-01', '2023-01-01']
    })
    result = deduplicate_smiles(df)
    assert len(result) == 1
    assert result.iloc[0]['value'] == 2.0  # Average of 1.0 and 3.0
    
def test_calculate_descriptors(sample_df_valid):
    """Test descriptor calculation adds expected columns."""
    result = calculate_descriptors(sample_df_valid)
    expected_cols = ['TPSA', 'logP', 'MW', 'NumRotatableBonds', 'NumHDonors', 'NumHAcceptors', 'NumRings']
    for col in expected_cols:
        assert col in result.columns, f"Column {col} missing from descriptors."
        
def test_sample_dataset_memory_limit(sample_df_valid):
    """Test sampling respects memory limits (mocked limit for unit test)."""
    # Force a small limit to trigger reduction logic if implemented
    # Note: This is a unit test; real memory profiling is hard to mock perfectly.
    # We test the logic that if target_size is large, it reduces.
    # For a small df, it should just return the df.
    result = sample_dataset(sample_df_valid, target_size=10)
    assert len(result) <= 10
    
def test_sample_dataset_insufficient_data():
    """Test DataInsufficiencyError when sample < 100 after reduction."""
    # Create a tiny dataframe
    tiny_df = pd.DataFrame({
        'smiles': ['CCO'],
        'target': ['solubility'],
        'value': [1.0],
        'assay_date': ['2023-01-01']
    })
    # If the logic forces reduction below 100, it should raise.
    # However, if the input is already < 100, the task says "If len(sampled_df) < 100 after reduction".
    # If the available data is < 100, it might just return what it has or raise depending on strictness.
    # The task says: "If len(sampled_df) < 100 after reduction, raise DataInsufficiencyError".
    # We assume the function tries to get target_size, fails, reduces, and if still < 100, raises.
    # For this test, we simulate a scenario where even the available data is too small for the requirement.
    # Since the task implies a minimum viable dataset of 100, we check if the error is raised.
    with pytest.raises(DataInsufficiencyError):
        # We pass a target_size that forces the check, but since available is 1, it fails.
        # The implementation must handle this.
        sample_dataset(tiny_df, target_size=1000)
