"""
Unit tests for aromaticity index calculation (US1).

This file contains tests expected to fail initially until the
implementation in code/descriptors.py is complete.
"""
import pytest
import numpy as np
from rdkit import Chem

# Import the function to be tested
# Note: This import will fail or the function will return None/0 until T015 is implemented
try:
    from code.descriptors import compute_huckel_aromaticity_index
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False

class TestAromaticityBenzene:
    """Tests for aromaticity index calculation on benzene."""
    
    def test_benzene_smiles_validity(self):
        """Verify that the benzene SMILES string is valid RDKit molecule."""
        smiles = "c1ccccc1"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Failed to parse benzene SMILES"
        assert mol.GetNumAtoms() == 6
        assert mol.GetNumBonds() == 6
    
    @pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation of compute_huckel_aromaticity_index not yet available")
    def test_benzene_aromaticity_index_nonzero(self):
        """
        Test that benzene yields a non-zero aromaticity index.
        
        Expected behavior: Benzene (c1ccccc1) is a classic aromatic system.
        The Hückel aromaticity index should return a positive value (e.g., > 0).
        """
        smiles = "c1ccccc1"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None
        
        index = compute_huckel_aromaticity_index(mol)
        
        # Assert the index is a valid number and greater than 0
        assert isinstance(index, (int, float, np.floating))
        assert index > 0.0, f"Expected positive aromaticity index for benzene, got {index}"
    
    @pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation of compute_huckel_aromaticity_index not yet available")
    def test_benzene_aromaticity_expected_range(self):
        """
        Test that benzene aromaticity index falls within expected theoretical range.
        
        For benzene, the Hückel method predicts a resonance energy of 2β.
        The normalized index should reflect significant aromatic character.
        """
        smiles = "c1ccccc1"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None
        
        index = compute_huckel_aromaticity_index(mol)
        
        # Benzene is highly aromatic; index should be substantial
        # This threshold is arbitrary but reflects strong aromaticity
        assert index > 1.0, f"Expected strong aromaticity for benzene (index > 1.0), got {index}"
    
    @pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation of compute_huckel_aromaticity_index not yet available")
    def test_cyclohexane_non_aromatic(self):
        """
        Test that a non-aromatic ring (cyclohexane) yields zero or near-zero index.
        
        This serves as a negative control to ensure the function distinguishes
        aromatic from non-aromatic systems.
        """
        smiles = "C1CCCCC1"  # Cyclohexane
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None
        
        index = compute_huckel_aromaticity_index(mol)
        
        # Cyclohexane is not aromatic; index should be 0 or very small
        assert index <= 0.05, f"Expected near-zero aromaticity for cyclohexane, got {index}"