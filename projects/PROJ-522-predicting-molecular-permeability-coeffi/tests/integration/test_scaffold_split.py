import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

# Import the function to test
from training import scaffold_split, get_murcko_scaffold

def test_get_murcko_scaffold_valid():
    """Test that Murcko scaffold extraction works for valid SMILES."""
    # Benzene
    smiles = "c1ccccc1"
    scaffold = get_murcko_scaffold(smiles)
    assert scaffold is not None
    assert scaffold != "invalid"
    
    # Ethanol (no ring, should return itself or empty ring system)
    smiles = "CCO"
    scaffold = get_murcko_scaffold(smiles)
    # RDKit returns the scaffold which might be just the ring system or the whole molecule if no rings
    assert scaffold is not None

def test_get_murcko_scaffold_invalid():
    """Test handling of invalid SMILES."""
    smiles = "invalid_smiles_string"
    scaffold = get_murcko_scaffold(smiles)
    assert scaffold == "invalid"

def test_scaffold_split_structure():
    """Test that scaffold split returns correct number of folds."""
    # Create dummy data
    data = pd.DataFrame({
        'smiles': ['c1ccccc1', 'c1ccccc1', 'CCO', 'CCO', 'CN', 'CN'],
        'target_mean': [1.0, 1.0, 2.0, 2.0, 3.0, 3.0]
    })
    
    folds = scaffold_split(data, n_splits=3)
    assert len(folds) == 3
    
    for train_df, val_df in folds:
        # Check that train and val are disjoint in terms of scaffolds
        # (This is a structural check, not a statistical one)
        assert len(train_df) > 0
        assert len(val_df) > 0

def test_scaffold_split_disjoint():
    """Test that train and validation sets do not share scaffolds."""
    data = pd.DataFrame({
        'smiles': [
            'c1ccccc1', # Scaffold A
            'c1ccccc1', # Scaffold A
            'CCO',      # Scaffold B
            'CN',       # Scaffold C
            'C(=O)O',   # Scaffold D
            'C(=O)O'    # Scaffold D
        ],
        'target_mean': [1, 1, 2, 3, 4, 4]
    })
    
    folds = scaffold_split(data, n_splits=2, seed=42)
    
    for train_df, val_df in folds:
        train_scaffolds = set(train_df['smiles'].apply(get_murcko_scaffold))
        val_scaffolds = set(val_df['smiles'].apply(get_murcko_scaffold))
        
        # There might be overlap if a molecule has multiple representations, 
        # but ideally, the scaffolds themselves should be disjoint.
        # However, since we split by scaffold, the sets of scaffolds should be disjoint.
        # Note: get_murcko_scaffold returns the scaffold string.
        # If the same scaffold string appears in both, it's a failure.
        
        # Re-calculate scaffolds for the split data to be sure
        # We need to re-calculate because the split function drops the 'scaffold' column
        # But we can re-calculate from smiles
        
        train_scaffolds = set(train_df['smiles'].apply(get_murcko_scaffold))
        val_scaffolds = set(val_df['smiles'].apply(get_murcko_scaffold))
        
        intersection = train_scaffolds.intersection(val_scaffolds)
        # Filter out "invalid" if present
        intersection.discard("invalid")
        
        assert len(intersection) == 0, f"Scaffolds {intersection} appear in both train and val"

def test_scaffold_split_empty_val():
    """Test that split does not produce empty validation sets if possible."""
    # Create data with many unique scaffolds
    smiles_list = [f"C{i}O" for i in range(100)] # 100 unique scaffolds
    data = pd.DataFrame({
        'smiles': smiles_list,
        'target_mean': list(range(100))
    })
    
    folds = scaffold_split(data, n_splits=5)
    
    for train_df, val_df in folds:
        assert len(val_df) > 0, "Validation set should not be empty"
        assert len(train_df) > 0, "Train set should not be empty"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
