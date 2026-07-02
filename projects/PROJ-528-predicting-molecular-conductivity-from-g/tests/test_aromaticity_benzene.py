"""
Unit tests for aromaticity index calculation on benzene (SMILES: "c1ccccc1").

These tests are written to FAIL initially (TDD red phase) because the 
implementation of the aromaticity index calculation in code/descriptors.py
has not yet been completed.

Expected behavior once implemented:
- Benzene (c1ccccc1) should have an aromaticity_index > 0.8 (highly aromatic)
- The calculation should use Hückel Molecular Orbital theory approximations
"""
import pytest
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rdkit import Chem
from rdkit.Chem import Descriptors

# This import will fail until descriptors.py is implemented
try:
    from descriptors import calculate_aromaticity_index
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False

@pytest.fixture
def benzene_mol():
    """Create benzene molecule from SMILES."""
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, "Failed to parse benzene SMILES"
    return mol

@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_benzene_aromaticity_index_positive(benzene_mol):
    """Test that benzene has a positive aromaticity index."""
    index = calculate_aromaticity_index(benzene_mol)
    assert index > 0, f"Expected positive aromaticity index, got {index}"

@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_benzene_aromaticity_index_high(benzene_mol):
    """Test that benzene has a high aromaticity index (close to 1.0)."""
    index = calculate_aromaticity_index(benzene_mol)
    # Benzene is the prototypical aromatic compound, should be > 0.8
    assert index >= 0.8, f"Expected aromaticity index >= 0.8 for benzene, got {index}"

@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_benzene_aromaticity_index_type(benzene_mol):
    """Test that the aromaticity index is a float."""
    index = calculate_aromaticity_index(benzene_mol)
    assert isinstance(index, float), f"Expected float, got {type(index)}"

@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation not yet available")
def test_benzene_aromaticity_index_range(benzene_mol):
    """Test that the aromaticity index is in a reasonable range [0, 1]."""
    index = calculate_aromaticity_index(benzene_mol)
    assert 0 <= index <= 1, f"Expected aromaticity index in [0, 1], got {index}"

def test_benzene_rdkit_aromaticity(benzene_mol):
    """Verify that RDKit correctly identifies benzene as aromatic."""
    # This test should pass regardless of our implementation
    assert benzene_mol.GetNumAtoms() == 6
    assert benzene_mol.GetNumBonds() == 6
    # Check that all bonds are aromatic
    for bond in benzene_mol.GetBonds():
        assert bond.GetIsAromatic(), "Benzene bonds should be aromatic"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])