import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

# Import the function to be implemented (expected to fail initially)
try:
    from descriptors import compute_conjugation_path_length
except ImportError:
    # Define a placeholder to allow test collection to proceed if module is missing
    # In a real run, this would be handled by the test runner skipping or failing import
    def compute_conjugation_path_length(mol):
        raise NotImplementedError("compute_conjugation_path_length not yet implemented")

def test_conjugation_path_length_butadiene_vs_butane():
    """
    Test that conjugation path length is significantly higher for conjugated
    butadiene (1,3-butadiene) compared to non-conjugated butane.

    Butadiene (C=CC=C) has a conjugated system of 4 carbons.
    Butane (CCCC) has no conjugation; max conjugated path is 1 (single bonds).
    """
    # SMILES for 1,3-butadiene (conjugated)
    smiles_butadiene = "C=CC=C"
    mol_butadiene = Chem.MolFromSmiles(smiles_butadiene)
    assert mol_butadiene is not None, "Failed to parse butadiene SMILES"

    # SMILES for butane (non-conjugated)
    smiles_butane = "CCCC"
    mol_butane = Chem.MolFromSmiles(smiles_butane)
    assert mol_butane is not None, "Failed to parse butane SMILES"

    # Compute conjugation path lengths
    # Expected: Butadiene > Butane
    # Butadiene should have a conjugation path length of roughly 4 (number of atoms in the chain)
    # Butane should have a conjugation path length of 1 (isolated single bonds don't form a conjugated system)
    length_butadiene = compute_conjugation_path_length(mol_butadiene)
    length_butane = compute_conjugation_path_length(mol_butane)

    # Assertion: Conjugated system must be strictly longer than non-conjugated
    # We expect a difference of at least 2 atoms to be significant
    assert length_butadiene > length_butane, (
        f"Conjugation path length for butadiene ({length_butadiene}) "
        f"must be greater than for butane ({length_butane}). "
        "This confirms the function correctly identifies conjugated systems."
    )

    # Additional sanity check: Butadiene should have a path length > 1
    assert length_butadiene > 1, (
        f"Butadiene conjugation path length ({length_butadiene}) should be > 1"
    )

    # Butane should effectively be 1 (single isolated bond/atom in terms of conjugation)
    # Depending on implementation, it might be 1 or 0, but strictly less than butadiene.
    assert length_butane < length_butadiene, (
        f"Butane conjugation path length ({length_butane}) should be less than butadiene"
    )