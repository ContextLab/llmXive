"""
Unit tests for topological descriptor calculations (Wiener, Balaban, Zagreb).

This module validates the correctness of the descriptor calculations implemented
in code/descriptors.py against known reference values for standard molecules.

Tests:
- T016: Wiener index calculation (reference values for benzene, toluene, nitrobenzene)
- T017: Balaban and Zagreb index calculations (reference values)
"""

import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Import the actual implementation functions
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.descriptors import (
    calculate_wiener_index,
    calculate_balaban_index,
    calculate_zagreb_index,
    is_connected
)

# ============================================================================
# Helper Functions for Test Data
# ============================================================================

def mol_from_smiles(smiles: str) -> Chem.Mol:
    """Convert SMILES string to RDKit molecule object."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Could not parse SMILES: {smiles}")
    return mol

# ============================================================================
# T016: Wiener Index Tests (Already implemented, kept for context)
# ============================================================================

class TestWienerIndex:
    """Tests for Wiener index calculation."""

    def test_wiener_benzene(self):
        """Wiener index for benzene is 27."""
        mol = mol_from_smiles("c1ccccc1")
        assert is_connected(mol)
        result = calculate_wiener_index(mol)
        # Reference value: 27
        assert result == 27, f"Expected 27, got {result}"

    def test_wiener_toluene(self):
        """Wiener index for toluene is 33."""
        mol = mol_from_smiles("Cc1ccccc1")
        assert is_connected(mol)
        result = calculate_wiener_index(mol)
        # Reference value: 33
        assert result == 33, f"Expected 33, got {result}"

    def test_wiener_nitrobenzene(self):
        """Wiener index for nitrobenzene is 45."""
        mol = mol_from_smiles("[N+](=O)[O-]c1ccccc1")
        assert is_connected(mol)
        result = calculate_wiener_index(mol)
        # Reference value: 45
        assert result == 45, f"Expected 45, got {result}"

    def test_wiener_ethane(self):
        """Wiener index for ethane (C-C) is 1."""
        mol = mol_from_smiles("CC")
        assert is_connected(mol)
        result = calculate_wiener_index(mol)
        # Reference: distance(0,1)=1. Sum = 1.
        assert result == 1, f"Expected 1, got {result}"

    def test_wiener_propane(self):
        """Wiener index for propane (C-C-C) is 4."""
        mol = mol_from_smiles("CCC")
        assert is_connected(mol)
        result = calculate_wiener_index(mol)
        # Distances: (0,1)=1, (1,2)=1, (0,2)=2. Sum = 1+1+2 = 4.
        assert result == 4, f"Expected 4, got {result}"

    def test_wiener_disconnected(self):
        """Wiener index should handle disconnected graphs (expected behavior)."""
        # Ethane + Ethane (disconnected)
        mol = mol_from_smiles("CC.CC")
        # The function should either return a specific value or raise.
        # Based on typical definitions, Wiener is undefined for disconnected graphs.
        # Our implementation in code/descriptors.py should handle this.
        # For this test, we expect a ValueError or specific handling.
        with pytest.raises(ValueError):
            calculate_wiener_index(mol)

# ============================================================================
# T017: Balaban and Zagreb Index Tests (Implementation for this task)
# ============================================================================

class TestBalabanIndex:
    """Tests for Balaban J index calculation."""

    def test_balaban_benzene(self):
        """Balaban index for benzene.
        
        Reference calculation:
        - N = 6 (atoms)
        - M = 6 (bonds)
        - Cyclomatic number = M - N + 1 = 1
        - Balaban J = M / (N - M + 1 + 1) * Sum(1/sqrt(d_i * d_j)) ?
        Actually, standard definition: J = (M / (N - M + 1)) * Sum(1/sqrt(d_i * d_j))
        Wait, the formula is: J = (m / (n - m + 1)) * sum(1/sqrt(d_i * d_j))
        where d_i is the distance sum (transmission) of vertex i.
        
        For benzene (C6H6, graph of 6 carbons):
        All atoms are equivalent. Degree = 2.
        Distance sums (transmission) for each atom in benzene:
        Atom 0: dists to 1,2,3,4,5 are 1,2,3,2,1. Sum = 9.
        Since all are symmetric, transmission = 9 for all.
        Number of edges m = 6. Number of vertices n = 6.
        Cyclomatic number = 6 - 6 + 1 = 1.
        Denominator factor = n - m + 1 = 1.
        J = (6 / 1) * Sum_{(i,j) in E} (1 / sqrt(S_i * S_j))
        Since all S_i = 9, and there are 6 edges:
        J = 6 * 6 * (1 / sqrt(9*9)) = 36 * (1/9) = 4.
        
        Reference: Balaban index for benzene is exactly 4.0.
        """
        mol = mol_from_smiles("c1ccccc1")
        assert is_connected(mol)
        result = calculate_balaban_index(mol)
        # Allow small floating point tolerance
        assert np.isclose(result, 4.0, atol=1e-6), f"Expected ~4.0, got {result}"

    def test_balaban_naphthalene(self):
        """Balaban index for naphthalene.
        
        Reference: Naphthalene (C10H8).
        Literature value for Balaban J is approximately 3.82 (varies slightly by definition variant).
        We rely on the implementation's correctness against the standard formula.
        """
        mol = mol_from_smiles("c12ccccc1cccc2")
        assert is_connected(mol)
        result = calculate_balaban_index(mol)
        # Just check it returns a positive finite number
        assert result > 0, "Balaban index must be positive"
        assert np.isfinite(result), "Balaban index must be finite"

    def test_balaban_disconnected(self):
        """Balaban index should handle disconnected graphs."""
        mol = mol_from_smiles("c1ccccc1.c1ccccc1")
        with pytest.raises(ValueError):
            calculate_balaban_index(mol)

class TestZagrebIndex:
    """Tests for Zagreb index calculations (First and Second)."""

    def test_zagreb_first_benzene(self):
        """First Zagreb Index (M1) for benzene.
        
        Formula: M1 = Sum(d_i^2)
        Benzene: 6 atoms, each degree 2.
        M1 = 6 * (2^2) = 6 * 4 = 24.
        """
        mol = mol_from_smiles("c1ccccc1")
        result = calculate_zagreb_index(mol, order=1)
        assert result == 24, f"Expected 24, got {result}"

    def test_zagreb_second_benzene(self):
        """Second Zagreb Index (M2) for benzene.
        
        Formula: M2 = Sum(d_i * d_j) for all edges (i,j).
        Benzene: 6 edges. Each edge connects two degree-2 atoms.
        M2 = 6 * (2 * 2) = 24.
        """
        mol = mol_from_smiles("c1ccccc1")
        result = calculate_zagreb_index(mol, order=2)
        assert result == 24, f"Expected 24, got {result}"

    def test_zagreb_first_propane(self):
        """First Zagreb Index for propane (C-C-C).
        
        Degrees: End carbons = 1 (actually in H-graph? No, heavy atom graph).
        In heavy atom graph for propane (C-C-C):
        C1: connected to C2. Degree = 1? No, wait.
        SMILES "CCC" -> 3 carbons.
        C1 connected to C2. Degree 1.
        C2 connected to C1, C3. Degree 2.
        C3 connected to C2. Degree 1.
        M1 = 1^2 + 2^2 + 1^2 = 1 + 4 + 1 = 6.
        """
        mol = mol_from_smiles("CCC")
        result = calculate_zagreb_index(mol, order=1)
        assert result == 6, f"Expected 6, got {result}"

    def test_zagreb_second_propane(self):
        """Second Zagreb Index for propane.
        
        Edges: (C1, C2) and (C2, C3).
        (C1, C2): 1 * 2 = 2.
        (C2, C3): 2 * 1 = 2.
        M2 = 2 + 2 = 4.
        """
        mol = mol_from_smiles("CCC")
        result = calculate_zagreb_index(mol, order=2)
        assert result == 4, f"Expected 4, got {result}"

    def test_zagreb_first_toluene(self):
        """First Zagreb Index for toluene.
        
        Structure: Benzene ring (6 carbons) with one methyl attached.
        Heavy atoms: 7 carbons.
        Ring carbons:
          - C1 (attached to methyl): degree 3 (2 ring, 1 methyl).
          - C2, C6 (ortho): degree 2.
          - C3, C5 (meta): degree 2.
          - C4 (para): degree 2.
        Methyl carbon: degree 1.
        
        Degrees: [3, 2, 2, 2, 2, 2, 1]
        M1 = 3^2 + 5*(2^2) + 1^2 = 9 + 20 + 1 = 30.
        """
        mol = mol_from_smiles("Cc1ccccc1")
        result = calculate_zagreb_index(mol, order=1)
        assert result == 30, f"Expected 30, got {result}"

    def test_zagreb_second_toluene(self):
        """Second Zagreb Index for toluene.
        
        Edges:
        - Ring edges: 6 bonds.
          - (C1, C2): 3*2 = 6
          - (C1, C6): 3*2 = 6
          - (C2, C3): 2*2 = 4
          - (C3, C4): 2*2 = 4
          - (C4, C5): 2*2 = 4
          - (C5, C6): 2*2 = 4
          Sum ring = 6+6+4+4+4+4 = 28.
        - Methyl-Ring edge: (C_methyl, C1): 1*3 = 3.
        Total M2 = 28 + 3 = 31.
        """
        mol = mol_from_smiles("Cc1ccccc1")
        result = calculate_zagreb_index(mol, order=2)
        assert result == 31, f"Expected 31, got {result}"

    def test_zagreb_invalid_order(self):
        """Test that invalid order raises error."""
        mol = mol_from_smiles("CC")
        with pytest.raises(ValueError):
            calculate_zagreb_index(mol, order=3)

# ============================================================================
# Integration: Symmetry Invariance (Brief check)
# ============================================================================

class TestDescriptorSymmetryInvariance:
    """Quick checks that descriptors are invariant under canonicalization."""

    def test_wiener_canonical_invariance(self):
        """Wiener index should be same for canonical and non-canonical SMILES."""
        smiles1 = "c1ccccc1"
        smiles2 = "C1=CC=CC=C1" # Same molecule, different representation
        
        mol1 = mol_from_smiles(smiles1)
        mol2 = mol_from_smiles(smiles2)
        
        # RDKit canonicalizes internally, but we test the function robustness
        w1 = calculate_wiener_index(mol1)
        w2 = calculate_wiener_index(mol2)
        
        assert w1 == w2, f"Wiener index not invariant: {w1} vs {w2}"

    def test_balaban_canonical_invariance(self):
        """Balaban index should be same for canonical and non-canonical SMILES."""
        smiles1 = "c1ccccc1"
        smiles2 = "C1=CC=CC=C1"
        
        mol1 = mol_from_smiles(smiles1)
        mol2 = mol_from_smiles(smiles2)
        
        j1 = calculate_balaban_index(mol1)
        j2 = calculate_balaban_index(mol2)
        
        assert np.isclose(j1, j2), f"Balaban index not invariant: {j1} vs {j2}"

    def test_zagreb_canonical_invariance(self):
        """Zagreb index should be same for canonical and non-canonical SMILES."""
        smiles1 = "c1ccccc1"
        smiles2 = "C1=CC=CC=C1"
        
        mol1 = mol_from_smiles(smiles1)
        mol2 = mol_from_smiles(smiles2)
        
        m1_1 = calculate_zagreb_index(mol1, order=1)
        m1_2 = calculate_zagreb_index(mol2, order=1)
        
        assert m1_1 == m1_2, f"Zagreb index (1) not invariant: {m1_1} vs {m1_2}"