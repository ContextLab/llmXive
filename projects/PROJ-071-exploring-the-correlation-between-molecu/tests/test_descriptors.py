"""
Unit tests for the descriptors module.
Verifies that calculated values match known reference values within RDKit precision.
"""
import pytest
from rdkit import Chem
from rdkit.Chem import Descriptors
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.descriptors import (
    validate_molecule,
    calculate_tpsa,
    calculate_rotatable_bonds,
    calculate_mw,
    calculate_aromatic_rings,
    calculate_wiener_index,
    calculate_zagreb_index,
    calculate_descriptors_for_molecule
)

# Reference SMILES from T010
REFERENCE_MOLECULES = [
    {
        "name": "Aspirin",
        "smiles": "CC(=O)Occcccc1C(=O)O",
        "expected_mw": 180.16,
        "expected_tpsa": 63.6,
        "expected_rotatable": 3,
        "expected_aromatic": 1
    },
    {
        "name": "Caffeine",
        "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
        "expected_mw": 194.19,
        "expected_tpsa": 58.4,
        "expected_rotatable": 0,
        "expected_aromatic": 1
    },
    {
        "name": "Diazepam",
        "smiles": "CN1C(=O)C=C(C2=CC=CC=C2Cl)N1C",
        "expected_mw": 284.75,
        "expected_tpsa": 32.7,
        "expected_rotatable": 1,
        "expected_aromatic": 2
    }
]

def test_validate_molecule_valid():
    """Test validation of valid SMILES strings."""
    for mol_data in REFERENCE_MOLECULES:
        mol, error = validate_molecule(mol_data["smiles"])
        assert mol is not None, f"Failed to validate {mol_data['name']}"
        assert error is None

def test_validate_molecule_invalid():
    """Test validation of invalid SMILES strings."""
    invalid_smiles = ["invalid_smiles", "C[C@H](O)C(=O)O", ""] # Second one is actually valid, let's use a truly invalid one
    invalid_smiles = ["invalid_smiles", "C1CCCC1", "C[C@H](O)C(=O)O"] # C1CCCC1 is valid. Let's use something definitely broken.
    invalid_smiles = ["invalid_smiles", "C1CC1CC", ""] # C1CC1CC is invalid valence on ring closure? No, just broken.
    # A known invalid SMILES: "C12C1C2" (too many ring closures)
    invalid_smiles = ["C12C1C2", ""]
    
    for smiles in invalid_smiles:
        mol, error = validate_molecule(smiles)
        # Should fail validation
        assert mol is None or error is not None

def test_calculate_mw():
    """Test Molecular Weight calculation against known values."""
    for mol_data in REFERENCE_MOLECULES:
        mol = Chem.MolFromSmiles(mol_data["smiles"])
        calculated_mw = calculate_mw(mol)
        # Allow small floating point tolerance
        assert abs(calculated_mw - mol_data["expected_mw"]) < 0.1, \
            f"MW mismatch for {mol_data['name']}: {calculated_mw} vs {mol_data['expected_mw']}"

def test_calculate_tpsa():
    """Test TPSA calculation."""
    for mol_data in REFERENCE_MOLECULES:
        mol = Chem.MolFromSmiles(mol_data["smiles"])
        calculated_tpsa = calculate_tpsa(mol)
        assert abs(calculated_tpsa - mol_data["expected_tpsa"]) < 0.5, \
            f"TPSA mismatch for {mol_data['name']}: {calculated_tpsa} vs {mol_data['expected_tpsa']}"

def test_calculate_rotatable_bonds():
    """Test Rotatable Bond Count."""
    for mol_data in REFERENCE_MOLECULES:
        mol = Chem.MolFromSmiles(mol_data["smiles"])
        calculated_rotatable = calculate_rotatable_bonds(mol)
        assert calculated_rotatable == mol_data["expected_rotatable"], \
            f"Rotatable bond mismatch for {mol_data['name']}: {calculated_rotatable} vs {mol_data['expected_rotatable']}"

def test_calculate_aromatic_rings():
    """Test Aromatic Ring Count."""
    for mol_data in REFERENCE_MOLECULES:
        mol = Chem.MolFromSmiles(mol_data["smiles"])
        calculated_aromatic = calculate_aromatic_rings(mol)
        assert calculated_aromatic == mol_data["expected_aromatic"], \
            f"Aromatic ring mismatch for {mol_data['name']}: {calculated_aromatic} vs {mol_data['expected_aromatic']}"

def test_calculate_wiener_index():
    """Test Wiener Index calculation (basic sanity check)."""
    for mol_data in REFERENCE_MOLECULES:
        mol = Chem.MolFromSmiles(mol_data["smiles"])
        wiener = calculate_wiener_index(mol)
        # Wiener index should be non-negative
        assert wiener >= 0, f"Wiener index should be non-negative for {mol_data['name']}"

def test_calculate_zagreb_index():
    """Test Zagreb Index calculation (basic sanity check)."""
    for mol_data in REFERENCE_MOLECULES:
        mol = Chem.MolFromSmiles(mol_data["smiles"])
        zagreb = calculate_zagreb_index(mol)
        # Zagreb index should be non-negative
        assert zagreb >= 0, f"Zagreb index should be non-negative for {mol_data['name']}"

def test_calculate_descriptors_for_molecule():
    """Test the full descriptor calculation pipeline for one molecule."""
    smiles = "CC(=O)Occcccc1C(=O)O" # Aspirin
    mol = Chem.MolFromSmiles(smiles)
    descriptors = calculate_descriptors_for_molecule(mol)
    
    assert "tpsa" in descriptors
    assert "rotatable_bonds" in descriptors
    assert "mw" in descriptors
    assert "aromatic_rings" in descriptors
    assert "wiener_index" in descriptors
    assert "zagreb_index" in descriptors
    
    assert abs(descriptors["mw"] - 180.16) < 0.1