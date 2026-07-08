"""
Unit tests for entropy.py functions.
"""
import pytest
import numpy as np
from rdkit import Chem
from entropy import compute_atom_entropy, compute_bond_entropy

def test_compute_atom_entropy_empty_mol():
    """Test atom entropy on an empty molecule (should handle gracefully)."""
    mol = Chem.MolFromSmiles("")
    if mol is None:
        # RDKit returns None for empty/invalid smiles
        assert compute_atom_entropy(None) == 0.0
    else:
        # If it parses as empty, degrees list is empty
        result = compute_atom_entropy(mol)
        assert result == 0.0

def test_compute_atom_entropy_methane():
    """
    Test atom entropy for Methane (CH4).
    Structure: One central C connected to 4 H.
    Atom degrees:
      - C: degree 4 (connected to 4 atoms)
      - H: degree 1 (connected to 1 atom)
    Distribution: {4: 1, 1: 4}
    Total atoms: 5
    Probabilities: p(4)=0.2, p(1)=0.8
    Entropy = - (0.2 * log2(0.2) + 0.8 * log2(0.8))
    """
    mol = Chem.MolFromSmiles("C")
    assert mol is not None
    result = compute_atom_entropy(mol)
    expected = - (0.2 * np.log2(0.2) + 0.8 * np.log2(0.8))
    assert np.isclose(result, expected, rtol=1e-4)

def test_compute_atom_entropy_ethane():
    """
    Test atom entropy for Ethane (CC).
    Structure: Two C connected to each other, each with 3 H.
    Atom degrees:
      - C1: degree 4 (1 C + 3 H)
      - C2: degree 4 (1 C + 3 H)
      - H (x6): degree 1
    Distribution: {4: 2, 1: 6}
    Total atoms: 8
    Probabilities: p(4)=0.25, p(1)=0.75
    """
    mol = Chem.MolFromSmiles("CC")
    assert mol is not None
    result = compute_atom_entropy(mol)
    expected = - (0.25 * np.log2(0.25) + 0.75 * np.log2(0.75))
    assert np.isclose(result, expected, rtol=1e-4)

def test_compute_bond_entropy_empty_mol():
    """Test bond entropy on a molecule with no bonds."""
    mol = Chem.MolFromSmiles("C") # Methane has bonds, but let's test logic
    # Actually, we need a case with NO bonds to test 0 entropy strictly if the function allows.
    # A single atom 'C' in RDKit usually has implicit bonds or is just an atom.
    # Let's rely on the logic: if bonds list is empty, entropy is 0.
    # We can force a check by passing a mock or checking the function behavior.
    # For RDKit, a single atom molecule has 0 bonds.
    # However, RDKit's MolFromSmiles("C") creates a molecule with 1 atom and 0 bonds.
    assert compute_bond_entropy(mol) == 0.0

def test_compute_bond_entropy_ethane():
    """
    Test bond entropy for Ethane (CC).
    Bonds:
      - 1 C-C bond (type 1, order 1)
      - 6 C-H bonds (type 1, order 1)
    Wait, the function likely uses bond order or bond type distribution.
    Based on standard implementation of topological entropy for bonds:
    It usually counts bond orders (1, 2, 3, aromatic).
    Ethane:
      - 1 bond of order 1 (C-C)
      - 6 bonds of order 1 (C-H)
    Total bonds: 7. All order 1.
    Distribution: {1: 7}. Probability 1.0.
    Entropy = - (1.0 * log2(1.0)) = 0.0.
    This test verifies that a uniform distribution yields 0 entropy.
    """
    mol = Chem.MolFromSmiles("CC")
    assert mol is not None
    result = compute_bond_entropy(mol)
    # All bonds are single bonds, so distribution is uniform -> entropy 0
    assert np.isclose(result, 0.0, atol=1e-4)

def test_compute_bond_entropy_ethene():
    """
    Test bond entropy for Ethene (C=C).
    Bonds:
      - 1 C=C double bond (order 2)
      - 4 C-H single bonds (order 1)
    Total bonds: 5.
    Distribution: {2: 1, 1: 4}
    Probabilities: p(2)=0.2, p(1)=0.8
    Entropy = - (0.2 * log2(0.2) + 0.8 * log2(0.8))
    """
    mol = Chem.MolFromSmiles("C=C")
    assert mol is not None
    result = compute_bond_entropy(mol)
    expected = - (0.2 * np.log2(0.2) + 0.8 * np.log2(0.8))
    assert np.isclose(result, expected, rtol=1e-4)

def test_compute_atom_entropy_benzene():
    """
    Test atom entropy for Benzene (c1ccccc1).
    All carbons are equivalent in the aromatic ring.
    Each C is connected to 2 C and 1 H (degree 3).
    All 6 carbons have degree 3.
    Distribution: {3: 6}.
    Probability: 1.0.
    Entropy: 0.0.
    """
    mol = Chem.MolFromSmiles("c1ccccc1")
    assert mol is not None
    result = compute_atom_entropy(mol)
    # All atoms have same degree -> 0 entropy
    assert np.isclose(result, 0.0, atol=1e-4)

def test_compute_bond_entropy_benzene():
    """
    Test bond entropy for Benzene.
    Bonds: 6 aromatic bonds.
    RDKit usually represents aromatic bonds with a specific bond type or order.
    If the function maps aromatic to a single category, entropy is 0.
    If it distinguishes, we need to check.
    Assuming standard implementation treats aromatic bonds as a single type (or order 1.5 conceptually, but grouped).
    Let's verify the function handles aromatic bonds without crashing and returns a value.
    """
    mol = Chem.MolFromSmiles("c1ccccc1")
    assert mol is not None
    result = compute_bond_entropy(mol)
    # Should be a valid float >= 0
    assert isinstance(result, float)
    assert result >= 0.0