"""
Unit tests for descriptor computation on mixed hybridization molecules (T012).

These tests are expected to fail initially as the implementation for mixed
hybridization handling in descriptors.py is not yet complete.
"""
import pytest
import pandas as pd
import numpy as np
from rdkit import Chem

# Import the function to be tested from the existing API surface
from code.descriptors import compute_descriptors_batch, compute_bond_order_annotation
from code.config import SEED

# Test molecules with mixed hybridization (sp, sp2, sp3)
MIXED_HYBRIDIZATION_MOLECULES = [
    # Propargyl alcohol: sp (C≡C), sp2 (C-OH), sp3 (CH2)
    {
        "smiles": "C#CCO",
        "name": "propargyl_alcohol",
        "expected_hybridizations": ["sp", "sp", "sp3", "sp3"]  # Approximate
    },
    # Vinyl acetylene: sp (C≡C), sp2 (C=C), sp3 (CH3)
    {
        "smiles": "C=CC#C",
        "name": "vinyl_acetylene",
        "expected_hybridizations": ["sp2", "sp2", "sp", "sp"]
    },
    # Allene: sp2 (C=C=C), sp3 (terminal CH2)
    {
        "smiles": "C=C=C",
        "name": "allene",
        "expected_hybridizations": ["sp2", "sp", "sp2"]
    },
    # Benzene with alkyne side chain: sp2 (aromatic), sp (alkyne)
    {
        "smiles": "c1ccccc1C#C",
        "name": "phenylacetylene",
        "expected_hybridizations": ["sp2", "sp2", "sp2", "sp2", "sp2", "sp2", "sp", "sp"]
    }
]

@pytest.mark.parametrize("mol_data", MIXED_HYBRIDIZATION_MOLECULES)
def test_descriptor_computation_mixed_hybridization(mol_data):
    """
    Test that descriptor computation handles molecules with mixed hybridization states.

    This test verifies:
    1. The molecule can be parsed from SMILES
    2. All required descriptors are computed without errors
    3. No NaN values appear in the output for valid molecules
    4. Bond order annotations reflect the mixed hybridization states

    Expected to fail until T020, T021, T022 implementations are complete.
    """
    smiles = mol_data["smiles"]
    mol = Chem.MolFromSmiles(smiles)

    assert mol is not None, f"Failed to parse SMILES: {smiles}"

    # Test batch descriptor computation
    df_input = pd.DataFrame({"smiles": [smiles]})

    # This should raise NotImplementedError or fail with missing descriptors
    # until the implementation is complete
    result_df = compute_descriptors_batch(df_input)

    # Verify required columns exist
    required_columns = [
        'smiles', 'status',
        'degree_mean', 'degree_std', 'degree_max', 'degree_min',
        'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
        'aromaticity_index', 'conjugation_length', 'ring_count',
        'bond_polarity', 'resonance_energy'
    ]

    for col in required_columns:
        assert col in result_df.columns, f"Missing required column: {col}"

    # Verify no NaN values for valid molecules
    valid_row = result_df[result_df['status'] == 'valid']
    if len(valid_row) > 0:
        assert not valid_row[required_columns[1:]].isna().any().any(), \
            "NaN values found in descriptor columns for valid molecule"

    # Test bond order annotation specifically for mixed hybridization
    mol_with_bonds = Chem.AddHs(mol)
    bond_annotations = compute_bond_order_annotation(mol_with_bonds)

    # Verify we get some bond annotations
    assert len(bond_annotations) > 0, "No bond annotations computed"

    # Check that we have different bond types (sp, sp2, sp3)
    bond_types = set([b['bond_type'] for b in bond_annotations])
    # At least 2 different bond types expected in mixed hybridization molecules
    assert len(bond_types) >= 2, \
        f"Expected at least 2 bond types in mixed hybridization, got {bond_types}"

def test_descriptor_computation_allene_specific():
    """
    Specific test for allene (C=C=C) which has a unique sp hybridization
    in the center carbon with orthogonal pi systems.
    """
    smiles = "C=C=C"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None

    df_input = pd.DataFrame({"smiles": [smiles]})

    # This test will fail until proper handling of allene's unique geometry
    result_df = compute_descriptors_batch(df_input)

    # Check for specific properties of allene
    assert 'conjugation_length' in result_df.columns
    assert 'aromaticity_index' in result_df.columns

    # Allene should have conjugation but not aromaticity
    # This assertion may fail until proper conjugation detection is implemented
    aromaticity = result_df['aromaticity_index'].iloc[0]
    assert aromaticity < 1.0, "Allene should not be aromatic"

def test_descriptor_computation_phenylacetylene():
    """
    Test phenylacetylene which combines aromatic (sp2) and alkyne (sp) systems.
    This is a challenging case for resonance energy estimation.
    """
    smiles = "c1ccccc1C#C"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None

    df_input = pd.DataFrame({"smiles": [smiles]})

    result_df = compute_descriptors_batch(df_input)

    # Verify ring count for benzene ring
    assert 'ring_count' in result_df.columns
    ring_count = result_df['ring_count'].iloc[0]
    assert ring_count >= 1, "Should detect at least one ring"

    # Verify resonance energy is computed (may be 0 or low until HMO implementation)
    assert 'resonance_energy' in result_df.columns
    resonance = result_df['resonance_energy'].iloc[0]
    # This will likely fail until proper HMO theory implementation
    assert resonance >= 0, "Resonance energy should be non-negative"

def test_mixed_hybridization_bond_polarity():
    """
    Test that bond polarity calculation works correctly for molecules
    with mixed hybridization and different electronegativity environments.
    """
    # Molecule with C, H, and O in different hybridization states
    smiles = "C#CCO"  # Propargyl alcohol
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None

    df_input = pd.DataFrame({"smiles": [smiles]})

    result_df = compute_descriptors_batch(df_input)

    # Check bond polarity column exists and has valid values
    assert 'bond_polarity' in result_df.columns
    bond_polarity = result_df['bond_polarity'].iloc[0]

    # Should be a positive number (Pauling scale difference * bond length)
    assert bond_polarity >= 0, "Bond polarity should be non-negative"

    # This test will fail until proper electronegativity and bond length
    # calculations are implemented for mixed hybridization
    assert bond_polarity > 0.0, "Expected non-zero bond polarity for polar bonds"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
