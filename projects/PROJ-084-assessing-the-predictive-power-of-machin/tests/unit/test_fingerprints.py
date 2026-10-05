"""
Unit tests for fingerprint generation (T016).
Verifies ECFP4 and MACCS dimensionality.
"""
import numpy as np
import pytest
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs

from code.preprocessing.fingerprints import generate_ecfp4, generate_maccs, ECFP_BITS, MACCS_BITS

def test_ecfp4_dimensionality():
    """Test that ECFP4 generates a vector of length 2048."""
    smiles = "CCO"  # Ethanol
    mol = Chem.MolFromSmiles(smiles)
    fp = generate_ecfp4(mol)
    
    assert isinstance(fp, np.ndarray), "FP should be numpy array"
    assert fp.dtype == bool, "FP should be boolean"
    assert len(fp) == ECFP_BITS, f"ECFP4 length should be {ECFP_BITS}, got {len(fp)}"

def test_maccs_dimensionality():
    """Test that MACCS generates a vector of length 167."""
    smiles = "CCO"  # Ethanol
    mol = Chem.MolFromSmiles(smiles)
    fp = generate_maccs(mol)
    
    assert isinstance(fp, np.ndarray), "FP should be numpy array"
    assert fp.dtype == bool, "FP should be boolean"
    assert len(fp) == MACCS_BITS, f"MACCS length should be {MACCS_BITS}, got {len(fp)}"

def test_ecfp4_consistency():
    """Test that same molecule produces same ECFP4."""
    smiles = "CC(=O)O"
    mol = Chem.MolFromSmiles(smiles)
    fp1 = generate_ecfp4(mol)
    fp2 = generate_ecfp4(mol)
    
    assert np.array_equal(fp1, fp2), "Same molecule should produce same fingerprint"

def test_maccs_consistency():
    """Test that same molecule produces same MACCS."""
    smiles = "CC(=O)O"
    mol = Chem.MolFromSmiles(smiles)
    fp1 = generate_maccs(mol)
    fp2 = generate_maccs(mol)
    
    assert np.array_equal(fp1, fp2), "Same molecule should produce same fingerprint"

def test_null_molecule_handling():
    """Test that None molecule returns zero vectors."""
    fp_ecfp = generate_ecfp4(None)
    fp_maccs = generate_maccs(None)
    
    assert len(fp_ecfp) == ECFP_BITS
    assert np.all(fp_ecfp == False)
    
    assert len(fp_maccs) == MACCS_BITS
    assert np.all(fp_maccs == False)