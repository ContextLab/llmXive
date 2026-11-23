"""
Unit tests for descriptor computation on mixed hybridization molecules.

These tests are expected to FAIL initially until the implementation
in code/descriptors.py is complete.
"""
import pytest
import pandas as pd
import numpy as np
from rdkit import Chem

# Import the descriptor functions from the implementation
from code.descriptors import (
    compute_descriptors_batch,
    compute_degree_statistics,
    compute_path_length_statistics,
    compute_ring_count,
    compute_huckel_aromaticity_index,
    compute_aromatic_ring_count,
    compute_bond_polarity,
    compute_resonance_energy
)


# Test molecules with mixed hybridization (sp2/sp3, aromatic/aliphatic)
MIXED_HYBRIDIZATION_MOLECULES = [
    # Toluene: aromatic ring (sp2) + methyl group (sp3)
    {
        "smiles": "Cc1ccccc1",
        "name": "toluene",
        "expected_features": {
            "has_aromatic": True,
            "has_aliphatic": True,
            "hybridization_mixed": True
        }
    },
    # Ethylbenzene: aromatic ring (sp2) + ethyl group (sp3)
    {
        "smiles": "CCc1ccccc1",
        "name": "ethylbenzene",
        "expected_features": {
            "has_aromatic": True,
            "has_aliphatic": True,
            "hybridization_mixed": True
        }
    },
    # 1-phenyl-1-propene: aromatic ring (sp2) + alkene (sp2) + alkyl (sp3)
    {
        "smiles": "CC=Cc1ccccc1",
        "name": "1-phenyl-1-propene",
        "expected_features": {
            "has_aromatic": True,
            "has_alkene": True,
            "has_aliphatic": True,
            "hybridization_mixed": True
        }
    },
    # Cyclohexylbenzene: aromatic ring (sp2) + cyclohexane (sp3)
    {
        "smiles": "C1CCCCC1c2ccccc2",
        "name": "cyclohexylbenzene",
        "expected_features": {
            "has_aromatic": True,
            "has_cycloalkane": True,
            "hybridization_mixed": True
        }
    },
    # Acetophenone: aromatic ring (sp2) + carbonyl (sp2) + methyl (sp3)
    {
        "smiles": "CC(=O)c1ccccc1",
        "name": "acetophenone",
        "expected_features": {
            "has_aromatic": True,
            "has_carbonyl": True,
            "has_aliphatic": True,
            "hybridization_mixed": True
        }
    }
]


def test_compute_descriptors_batch_returns_dataframe():
    """Test that compute_descriptors_batch returns a DataFrame with expected columns."""
    smiles_list = [m["smiles"] for m in MIXED_HYBRIDIZATION_MOLECULES]
    
    # This will fail if the function is not implemented or returns wrong type
    result = compute_descriptors_batch(smiles_list)
    
    assert isinstance(result, pd.DataFrame), "Result should be a pandas DataFrame"
    assert len(result) == len(smiles_list), "Result should have same number of rows as input"
    
    # Check for required columns (from task T019 specification)
    required_columns = [
        'smiles', 'status', 'degree_mean', 'degree_std', 'degree_max', 'degree_min',
        'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
        'aromaticity_index', 'conjugation_length', 'ring_count',
        'bond_polarity', 'resonance_energy'
    ]
    
    for col in required_columns:
        assert col in result.columns, f"Missing required column: {col}"


def test_mixed_hybridization_molecules_have_valid_descriptors():
    """Test that mixed hybridization molecules produce valid numeric descriptors."""
    smiles_list = [m["smiles"] for m in MIXED_HYBRIDIZATION_MOLECULES]
    
    result = compute_descriptors_batch(smiles_list)
    
    # All rows should have status 'valid'
    valid_rows = result[result['status'] == 'valid']
    assert len(valid_rows) == len(smiles_list), "All molecules should be valid"
    
    # Check that numeric columns contain valid numbers (no NaN)
    numeric_cols = [
        'degree_mean', 'degree_std', 'degree_max', 'degree_min',
        'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
        'aromaticity_index', 'conjugation_length', 'ring_count',
        'bond_polarity', 'resonance_energy'
    ]
    
    for col in numeric_cols:
        assert not result[col].isna().any(), f"Column {col} contains NaN values"
        assert result[col].dtype in [np.float64, np.int64, np.float32, np.int32], \
            f"Column {col} should be numeric"


def test_aromaticity_detection_in_mixed_systems():
    """Test that aromaticity index correctly identifies aromatic rings in mixed systems."""
    smiles_list = [m["smiles"] for m in MIXED_HYBRIDIZATION_MOLECULES]
    
    result = compute_descriptors_batch(smiles_list)
    
    # All test molecules contain at least one aromatic ring
    # So aromaticity_index should be > 0 for all
    assert (result['aromaticity_index'] > 0).all(), \
        "All mixed hybridization molecules should have non-zero aromaticity index"
    
    # Ring count should be at least 1 (the aromatic ring)
    assert (result['ring_count'] >= 1).all(), \
        "All molecules should have at least 1 ring"


def test_bond_polarity_varies_with_hybridization():
    """Test that bond polarity descriptor captures differences in hybridization environments."""
    smiles_list = [m["smiles"] for m in MIXED_HYBRIDIZATION_MOLECULES]
    
    result = compute_descriptors_batch(smiles_list)
    
    # Bond polarity should be positive for all valid molecules
    assert (result['bond_polarity'] > 0).all(), \
        "Bond polarity should be positive for all valid molecules"
    
    # There should be variation in bond polarity across different molecules
    assert result['bond_polarity'].std() > 0, \
        "Bond polarity should vary across different mixed hybridization molecules"


def test_resonance_energy_higher_for_conjugated_systems():
    """Test that resonance energy is higher for molecules with extended conjugation."""
    # Compare toluene (single aromatic ring) vs 1-phenyl-1-propene (aromatic + conjugated alkene)
    toluene_smiles = "Cc1ccccc1"
    conjugated_smiles = "CC=Cc1ccccc1"
    
    result = compute_descriptors_batch([toluene_smiles, conjugated_smiles])
    
    toluene_row = result[result['smiles'] == toluene_smiles].iloc[0]
    conjugated_row = result[result['smiles'] == conjugated_smiles].iloc[0]
    
    # Conjugated system should have higher resonance energy
    # This test may fail if the resonance energy calculation is not implemented correctly
    assert conjugated_row['resonance_energy'] >= toluene_row['resonance_energy'], \
        "Conjugated systems should have higher or equal resonance energy"


def test_degree_statistics_for_mixed_hybridization():
    """Test that degree statistics capture the structural differences in mixed systems."""
    smiles_list = [m["smiles"] for m in MIXED_HYBRIDIZATION_MOLECULES]
    
    result = compute_descriptors_batch(smiles_list)
    
    # Degree statistics should be non-negative
    for col in ['degree_mean', 'degree_std', 'degree_max', 'degree_min']:
        assert (result[col] >= 0).all(), f"{col} should be non-negative"
    
    # There should be variation across different molecules
    for col in ['degree_mean', 'degree_std', 'degree_max', 'degree_min']:
        assert result[col].std() > 0, f"{col} should vary across molecules"


def test_path_length_statistics_for_mixed_hybridization():
    """Test that path length statistics capture molecular size and shape."""
    smiles_list = [m["smiles"] for m in MIXED_HYBRIDIZATION_MOLECULES]
    
    result = compute_descriptors_batch(smiles_list)
    
    # Path length statistics should be non-negative
    for col in ['path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min']:
        assert (result[col] >= 0).all(), f"{col} should be non-negative"
    
    # Larger molecules should have longer path lengths
    # Ethylbenzene should have longer paths than toluene
    toluene_row = result[result['smiles'] == "Cc1ccccc1"].iloc[0]
    ethylbenzene_row = result[result['smiles'] == "CCc1ccccc1"].iloc[0]
    
    # This is a soft assertion - implementation details may vary
    assert ethylbenzene_row['path_length_mean'] >= toluene_row['path_length_mean'], \
        "Larger molecules should have longer average path lengths"