"""
Unit tests for RDKit descriptor calculation.
"""
import pytest
from rdkit import Chem
from code.data.descriptors import calculate_descriptors

@pytest.fixture
def valid_smiles():
    return "CCO"  # Ethanol

@pytest.fixture
def invalid_smiles():
    return "invalid_smiles_string"

def test_calculate_descriptors_valid_molecule(valid_smiles):
    """Test that descriptors are calculated correctly for a valid molecule."""
    mol = Chem.MolFromSmiles(valid_smiles)
    assert mol is not None, "Failed to parse valid SMILES"
    
    result = calculate_descriptors(mol)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "molecular_weight" in result, "Missing molecular_weight"
    assert "polar_surface_area" in result, "Missing polar_surface_area"
    assert "polarizability" in result, "Missing polarizability"
    assert "h_bond_donors" in result, "Missing h_bond_donors"
    assert "h_bond_acceptors" in result, "Missing h_bond_acceptors"
    assert "van_der_waals_volume" in result, "Missing van_der_waals_volume"
    assert "kinetic_diameter" in result, "Missing kinetic_diameter"
    
    # Check that values are numeric
    for key, value in result.items():
        assert isinstance(value, (int, float)), f"Value for {key} should be numeric"
    
    # Basic sanity checks for ethanol
    assert result["molecular_weight"] > 0
    assert result["h_bond_donors"] >= 1  # Ethanol has at least one OH group
    assert result["h_bond_acceptors"] >= 1

def test_calculate_descriptors_invalid_molecule(invalid_smiles):
    """Test that an error is raised for invalid SMILES."""
    mol = Chem.MolFromSmiles(invalid_smiles)
    assert mol is None, "Invalid SMILES should return None"
    
    with pytest.raises(ValueError, match="Invalid molecule"):
        calculate_descriptors(mol)

def test_calculate_descriptors_none_molecule():
    """Test that an error is raised for None input."""
    with pytest.raises(ValueError, match="Invalid molecule"):
        calculate_descriptors(None)

def test_descriptor_ranges():
    """Test that calculated descriptors are within reasonable ranges."""
    # Test with a simple molecule: methane
    mol = Chem.MolFromSmiles("C")
    result = calculate_descriptors(mol)
    
    # Molecular weight of methane is ~16
    assert 10 < result["molecular_weight"] < 25
    
    # Test with a larger molecule: benzene
    mol = Chem.MolFromSmiles("c1ccccc1")
    result = calculate_descriptors(mol)
    
    # Molecular weight of benzene is ~78
    assert 70 < result["molecular_weight"] < 85
