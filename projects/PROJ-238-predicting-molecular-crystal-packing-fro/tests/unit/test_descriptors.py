import pytest
from rdkit import Chem
from code.utils.descriptors import compute_descriptors

def test_benzene_volume():
    """
    Verify that the Volume for benzene is between 50 and 150 Angstroms^3.
    Benzene SMILES: c1ccccc1
    """
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, "Failed to parse benzene SMILES"
    
    # The compute_descriptors function handles 3D generation internally if needed
    desc = compute_descriptors(mol)
    
    volume = desc["Volume"]
    assert 50.0 <= volume <= 150.0, f"Benzene volume {volume} is not in expected range [50, 150]"
    
def test_descriptors_keys():
    """Verify that all required keys are present."""
    mol = Chem.MolFromSmiles("CCO") # Ethanol
    desc = compute_descriptors(mol)
    
    required_keys = ["Volume", "SurfaceArea", "Dipole", "HBA", "HBD", "PSA"]
    for key in required_keys:
        assert key in desc, f"Missing key: {key}"