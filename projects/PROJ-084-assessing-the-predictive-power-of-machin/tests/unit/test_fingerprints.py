"""
Unit tests for fingerprint dimensionality validation.

Verifies that:
- ECFP4 fingerprints have exactly 2048 dimensions
- MACCS fingerprints have exactly 167 dimensions
"""
import pytest
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
import numpy as np

from code.preprocessing.fingerprints import generate_ecfp4, generate_maccs


@pytest.fixture
def sample_smiles():
    """Provide a simple, valid SMILES string for testing."""
    # Caffeine is a stable, common molecule
    return "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"


@pytest.fixture
def sample_mol(sample_smiles):
    """Convert SMILES to RDKit Mol object."""
    mol = Chem.MolFromSmiles(sample_smiles)
    assert mol is not None, "Failed to parse sample SMILES"
    return mol


def test_ecfp4_dimensionality(sample_mol):
    """Test that ECFP4 fingerprints produce exactly 2048 bits."""
    fp = generate_ecfp4(sample_mol)
    assert fp is not None, "ECFP4 fingerprint generation failed"
    
    # Convert to numpy array to check length
    fp_array = np.array(fp)
    assert len(fp_array) == 2048, (
        f"ECFP4 dimensionality mismatch: expected 2048, got {len(fp_array)}"
    )


def test_maccs_dimensionality(sample_mol):
    """Test that MACCS fingerprints produce exactly 167 bits."""
    fp = generate_maccs(sample_mol)
    assert fp is not None, "MACCS fingerprint generation failed"
    
    # Convert to numpy array to check length
    fp_array = np.array(fp)
    # Note: MACCS keys in RDKit are 167 bits (index 0 is unused, 1-166 are used)
    assert len(fp_array) == 167, (
        f"MACCS dimensionality mismatch: expected 167, got {len(fp_array)}"
    )


def test_ecfp4_consistency(sample_smiles):
    """Test that ECFP4 generation is deterministic for the same input."""
    mol1 = Chem.MolFromSmiles(sample_smiles)
    mol2 = Chem.MolFromSmiles(sample_smiles)
    
    fp1 = generate_ecfp4(mol1)
    fp2 = generate_ecfp4(mol2)
    
    assert np.array_equal(fp1, fp2), "ECFP4 generation is not deterministic"


def test_maccs_consistency(sample_smiles):
    """Test that MACCS generation is deterministic for the same input."""
    mol1 = Chem.MolFromSmiles(sample_smiles)
    mol2 = Chem.MolFromSmiles(sample_smiles)
    
    fp1 = generate_maccs(mol1)
    fp2 = generate_maccs(mol2)
    
    assert np.array_equal(fp1, fp2), "MACCS generation is not deterministic"


def test_different_molecules_different_fingerprints():
    """Test that different molecules produce different fingerprints."""
    smiles1 = "CCO"  # Ethanol
    smiles2 = "CCCO"  # Propanol
    
    mol1 = Chem.MolFromSmiles(smiles1)
    mol2 = Chem.MolFromSmiles(smiles2)
    
    ecfp1 = generate_ecfp4(mol1)
    ecfp2 = generate_ecfp4(mol2)
    
    maccs1 = generate_maccs(mol1)
    maccs2 = generate_maccs(mol2)
    
    assert not np.array_equal(ecfp1, ecfp2), "Different molecules should have different ECFP4"
    assert not np.array_equal(maccs1, maccs2), "Different molecules should have different MACCS"
