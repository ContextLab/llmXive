"""
Integration test for scaffold split ensuring no structural leakage (T023).

This test verifies that the scaffold split implementation correctly separates
molecules by their Murcko scaffolds, ensuring that no molecule with the same
scaffold appears in both training and test sets.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.scaffold_split import get_murcko_scaffold, scaffold_split
from code.config import SEED


def create_test_dataset():
    """
    Create a test dataset with known scaffolds to verify splitting behavior.
    Includes molecules that share scaffolds to test for leakage.
    """
    # Molecules with shared scaffolds (benzene ring)
    smiles_list = [
        "c1ccccc1",           # Benzene - Scaffold 1
        "c1ccccc1C",          # Toluene - Scaffold 1 (same core)
        "c1ccccc1CC",         # Ethylbenzene - Scaffold 1
        "c1ccccc1O",          # Phenol - Scaffold 1
        "c1ccccc1N",          # Aniline - Scaffold 1
        
        # Different scaffold (pyridine)
        "c1ccncc1",           # Pyridine - Scaffold 2
        "c1ccncc1C",          # Methylpyridine - Scaffold 2
        
        # Aliphatic chain (no ring)
        "CCCCC",              # Pentane - Scaffold 3
        "CCCCCC",             # Hexane - Scaffold 3
        
        # Another aromatic system
        "c1cccc2ccccc12",     # Naphthalene - Scaffold 4
        "c1cccc2ccccc12C",    # Methylnaphthalene - Scaffold 4
    ]
    
    # Create target values (conductivity-like)
    targets = np.random.RandomState(SEED).uniform(-5.0, 0.0, size=len(smiles_list))
    
    df = pd.DataFrame({
        'smiles': smiles_list,
        'conductivity': targets
    })
    
    return df


def test_scaffold_extraction():
    """Test that Murcko scaffolds are correctly extracted."""
    mol = Chem.MolFromSmiles("c1ccccc1C")
    scaffold = get_murcko_scaffold(mol)
    
    # Benzene ring should be the scaffold (without side chain)
    assert scaffold is not None
    scaffold_smiles = Chem.MolToSmiles(scaffold)
    assert "c1ccccc1" in scaffold_smiles or "C1=CC=CC=C1" in scaffold_smiles


def test_no_scaffold_leakage():
    """
    Integration test: Verify that no scaffold appears in both train and test sets.
    This is the core requirement for preventing structural leakage.
    """
    df = create_test_dataset()
    
    # Perform scaffold split
    train_df, test_df = scaffold_split(df, test_size=0.3, seed=SEED)
    
    # Extract scaffolds for all molecules
    train_scaffolds = set()
    test_scaffolds = set()
    
    for smiles in train_df['smiles']:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            scaffold = get_murcko_scaffold(mol)
            if scaffold:
                scaffold_smiles = Chem.MolToSmiles(scaffold)
                train_scaffolds.add(scaffold_smiles)
    
    for smiles in test_df['smiles']:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            scaffold = get_murcko_scaffold(mol)
            if scaffold:
                scaffold_smiles = Chem.MolToSmiles(scaffold)
                test_scaffolds.add(scaffold_smiles)
    
    # Check for intersection (leakage)
    intersection = train_scaffolds.intersection(test_scaffolds)
    
    assert len(intersection) == 0, (
        f"Scaffold leakage detected! Shared scaffolds: {intersection}\n"
        f"Train scaffolds: {train_scaffolds}\n"
        f"Test scaffolds: {test_scaffolds}"
    )


def test_split_ratio():
    """Test that the split approximately maintains the requested ratio."""
    df = create_test_dataset()
    train_df, test_df = scaffold_split(df, test_size=0.3, seed=SEED)
    
    total = len(df)
    train_ratio = len(train_df) / total
    test_ratio = len(test_df) / total
    
    # Allow some tolerance due to scaffold grouping
    assert 0.25 <= train_ratio <= 0.85, f"Train ratio {train_ratio} outside expected range"
    assert 0.15 <= test_ratio <= 0.75, f"Test ratio {test_ratio} outside expected range"
    
    # Verify no overlap in indices
    train_indices = set(train_df.index)
    test_indices = set(test_df.index)
    assert len(train_indices.intersection(test_indices)) == 0


def test_deterministic_split():
    """Test that the same seed produces the same split."""
    df = create_test_dataset()
    
    train_df1, test_df1 = scaffold_split(df, test_size=0.3, seed=SEED)
    train_df2, test_df2 = scaffold_split(df, test_size=0.3, seed=SEED)
    
    # Should be identical
    pd.testing.assert_frame_equal(train_df1.sort_values('smiles').reset_index(drop=True),
                                 train_df2.sort_values('smiles').reset_index(drop=True))
    pd.testing.assert_frame_equal(test_df1.sort_values('smiles').reset_index(drop=True),
                                 test_df2.sort_values('smiles').reset_index(drop=True))


def test_realistic_scenario_with_leaked_scaffold():
    """
    Test that the algorithm correctly handles a dataset where some scaffolds
    would naturally leak if not properly split.
    """
    # Create a dataset with clear scaffold groups
    df = create_test_dataset()
    
    # Get all scaffolds
    scaffold_map = {}
    for idx, smiles in enumerate(df['smiles']):
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            scaffold = get_murcko_scaffold(mol)
            if scaffold:
                scaffold_smiles = Chem.MolToSmiles(scaffold)
                if scaffold_smiles not in scaffold_map:
                    scaffold_map[scaffold_smiles] = []
                scaffold_map[scaffold_smiles].append(idx)
    
    # Verify we have multiple molecules sharing scaffolds
    multi_member_scaffolds = {k: v for k, v in scaffold_map.items() if len(v) > 1}
    assert len(multi_member_scaffolds) > 0, "Test dataset should have shared scaffolds"
    
    # Perform split
    train_df, test_df = scaffold_split(df, test_size=0.3, seed=SEED)
    
    # Verify no scaffold appears in both sets
    train_scaffold_indices = set()
    test_scaffold_indices = set()
    
    for smiles in train_df['smiles']:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            scaffold = get_murcko_scaffold(mol)
            if scaffold:
                scaffold_smiles = Chem.MolToSmiles(scaffold)
                train_scaffold_indices.add(scaffold_smiles)
    
    for smiles in test_df['smiles']:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            scaffold = get_murcko_scaffold(mol)
            if scaffold:
                scaffold_smiles = Chem.MolToSmiles(scaffold)
                test_scaffold_indices.add(scaffold_smiles)
    
    # Check intersection
    shared = train_scaffold_indices.intersection(test_scaffold_indices)
    assert len(shared) == 0, f"Scaffold leakage detected: {shared}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
