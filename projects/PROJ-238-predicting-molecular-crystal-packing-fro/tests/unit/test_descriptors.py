import pytest
from rdkit import Chem
from code.utils.descriptors import compute_descriptors

def test_benzene_descriptors():
    """Test descriptor computation for benzene (c1ccccc1)."""
    mol = Chem.MolFromSmiles("c1ccccc1")
    assert mol is not None, "Failed to parse benzene SMILES"
    
    descriptors = compute_descriptors(mol)
    
    # Check that all required keys are present
    required_keys = ["Volume", "SurfaceArea", "Dipole", "HBA", "HBD", "PSA"]
    for key in required_keys:
        assert key in descriptors, f"Missing key: {key}"
    
    # Verify Volume is between 50 and 150 Angstrom^3 (as per T005 verification)
    # Note: The actual value depends on the calculation method (MR proxy vs CalcMolVolume)
    # We expect a reasonable value in this range.
    assert 50 <= descriptors["Volume"] <= 150, f"Volume {descriptors['Volume']} is not in [50, 150]"
    
    # Verify HBA and HBD are 0 for benzene
    assert descriptors["HBA"] == 0, f"HBA should be 0 for benzene, got {descriptors['HBA']}"
    assert descriptors["HBD"] == 0, f"HBD should be 0 for benzene, got {descriptors['HBD']}"
    
    # Verify PSA is 0 for benzene (non-polar)
    assert descriptors["PSA"] == 0.0, f"PSA should be 0.0 for benzene, got {descriptors['PSA']}"

def test_water_descriptors():
    """Test descriptor computation for water (O)."""
    mol = Chem.MolFromSmiles("O")
    assert mol is not None, "Failed to parse water SMILES"
    
    descriptors = compute_descriptors(mol)
    
    # HBA should be 1 (oxygen has 2 lone pairs, but Lipinski counts it as 1 acceptor)
    assert descriptors["HBA"] == 1, f"HBA should be 1 for water, got {descriptors['HBA']}"
    # HBD should be 2 (two hydrogens)
    assert descriptors["HBD"] == 2, f"HBD should be 2 for water, got {descriptors['HBD']}"
    # PSA should be > 0
    assert descriptors["PSA"] > 0, f"PSA should be > 0 for water, got {descriptors['PSA']}"

def test_null_molecule():
    """Test that compute_descriptors handles None input gracefully."""
    result = compute_descriptors(None)
    assert result["Volume"] == 0.0
    assert result["SurfaceArea"] == 0.0
    assert result["Dipole"] == 0.0
    assert result["HBA"] == 0
    assert result["HBD"] == 0
    assert result["PSA"] == 0.0
