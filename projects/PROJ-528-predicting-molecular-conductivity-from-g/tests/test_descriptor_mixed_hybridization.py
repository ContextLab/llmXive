"""
Unit tests for descriptor computation on mixed hybridization molecules.

These tests are expected to fail initially as the implementation for mixed
hybridization handling is not yet complete.
"""
import pytest
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

# Import the descriptor functions from the implementation
from descriptors import (
    compute_degree_statistics,
    compute_path_length_statistics,
    compute_ring_count,
    compute_huckel_aromaticity_index,
    compute_aromatic_ring_count,
    compute_bond_order_annotation,
    compute_bond_polarity,
    compute_resonance_energy
)

# Sample molecules with mixed hybridization
MIXED_HYBRIDIZATION_MOLECULES = [
    # Propene: sp2 and sp3 carbons
    {
        "name": "propene",
        "smiles": "C=CC",
        "expected_hybridization_mix": {"sp2": 2, "sp3": 1}
    },
    # Acetone: sp2 carbonyl carbon and sp3 methyl carbons
    {
        "name": "acetone",
        "smiles": "CC(=O)C",
        "expected_hybridization_mix": {"sp2": 1, "sp3": 2}
    },
    # Acrylonitrile: sp2 carbons and sp nitrogen
    {
        "name": "acrylonitrile",
        "smiles": "C=CC#N",
        "expected_hybridization_mix": {"sp2": 2, "sp": 1, "sp3": 1}
    },
    # Benzene with methyl group (toluene): aromatic and sp3
    {
        "name": "toluene",
        "smiles": "Cc1ccccc1",
        "expected_hybridization_mix": {"aromatic": 6, "sp3": 1}
    }
]

@pytest.fixture
def mixed_hybridization_df():
    """Create a DataFrame with mixed hybridization molecules."""
    data = []
    for mol_info in MIXED_HYBRIDIZATION_MOLECULES:
        mol = Chem.MolFromSmiles(mol_info["smiles"])
        data.append({
            "name": mol_info["name"],
            "smiles": mol_info["smiles"],
            "mol": mol,
            "expected_mix": mol_info["expected_hybridization_mix"]
        })
    return pd.DataFrame(data)

def test_compute_degree_statistics_mixed_hybridization(mixed_hybridization_df):
    """Test degree statistics computation on mixed hybridization molecules."""
    for _, row in mixed_hybridization_df.iterrows():
        mol = row["mol"]
        assert mol is not None, f"Failed to parse SMILES for {row['name']}"
        
        # This should not raise an error
        degree_stats = compute_degree_statistics(mol)
        
        # Check that all expected keys are present
        expected_keys = ["mean", "std", "max", "min"]
        for key in expected_keys:
            assert key in degree_stats, f"Missing {key} in degree statistics for {row['name']}"
            assert isinstance(degree_stats[key], (int, float)), f"{key} should be numeric for {row['name']}"

def test_compute_path_length_statistics_mixed_hybridization(mixed_hybridization_df):
    """Test path length statistics on mixed hybridization molecules."""
    for _, row in mixed_hybridization_df.iterrows():
        mol = row["mol"]
        assert mol is not None, f"Failed to parse SMILES for {row['name']}"
        
        path_stats = compute_path_length_statistics(mol)
        
        expected_keys = ["mean", "std", "max", "min"]
        for key in expected_keys:
            assert key in path_stats, f"Missing {key} in path length statistics for {row['name']}"
            assert isinstance(path_stats[key], (int, float)), f"{key} should be numeric for {row['name']}"

def test_compute_huckel_aromaticity_mixed_hybridization(mixed_hybridization_df):
    """Test Hückel aromaticity index on molecules with mixed hybridization."""
    for _, row in mixed_hybridization_df.iterrows():
        mol = row["mol"]
        assert mol is not None, f"Failed to parse SMILES for {row['name']}"
        
        # This should handle mixed hybridization without crashing
        huckel_index = compute_huckel_aromaticity_index(mol)
        
        # Should return a numeric value
        assert isinstance(huckel_index, (int, float)), f"Hückel index should be numeric for {row['name']}"

def test_compute_bond_polarity_mixed_hybridization(mixed_hybridization_df):
    """Test bond polarity computation on mixed hybridization molecules."""
    for _, row in mixed_hybridization_df.iterrows():
        mol = row["mol"]
        assert mol is not None, f"Failed to parse SMILES for {row['name']}"
        
        bond_polarity = compute_bond_polarity(mol)
        
        # Should return a numeric value
        assert isinstance(bond_polarity, (int, float)), f"Bond polarity should be numeric for {row['name']}"

def test_compute_resonance_energy_mixed_hybridization(mixed_hybridization_df):
    """Test resonance energy computation on mixed hybridization molecules."""
    for _, row in mixed_hybridization_df.iterrows():
        mol = row["mol"]
        assert mol is not None, f"Failed to parse SMILES for {row['name']}"
        
        resonance_energy = compute_resonance_energy(mol)
        
        # Should return a numeric value
        assert isinstance(resonance_energy, (int, float)), f"Resonance energy should be numeric for {row['name']}"

def test_hybridization_specific_behavior(mixed_hybridization_df):
    """Test that descriptors capture hybridization-specific differences."""
    # Propene should have different characteristics than toluene due to hybridization
    propene_row = mixed_hybridization_df[mixed_hybridization_df["name"] == "propene"].iloc[0]
    toluene_row = mixed_hybridization_df[mixed_hybridization_df["name"] == "toluene"].iloc[0]
    
    propene_mol = propene_row["mol"]
    toluene_mol = toluene_row["mol"]
    
    # Compute descriptors
    propene_resonance = compute_resonance_energy(propene_mol)
    toluene_resonance = compute_resonance_energy(toluene_mol)
    
    # Toluene has aromatic resonance, propene does not
    # This test expects them to be different (but implementation may not yet capture this correctly)
    assert propene_resonance != toluene_resonance, \
        "Resonance energy should differ between propene (non-aromatic) and toluene (aromatic)"

def test_bond_order_annotation_mixed_hybridization(mixed_hybridization_df):
    """Test bond order annotation on molecules with mixed bond types."""
    for _, row in mixed_hybridization_df.iterrows():
        mol = row["mol"]
        assert mol is not None, f"Failed to parse SMILES for {row['name']}"
        
        bond_orders = compute_bond_order_annotation(mol)
        
        # Should return a list or dict of bond orders
        assert bond_orders is not None, f"Bond orders should not be None for {row['name']}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])