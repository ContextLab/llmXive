"""
Unit tests for aromaticity index calculation.
Expected to fail initially as the implementation in code/descriptors.py
is not yet complete or may not match the expected behavior.
"""
import pytest
import numpy as np
from rdkit import Chem
from code.descriptors import compute_huckel_aromaticity_index

def test_aromaticity_benzene():
    """
    Test Hückel aromaticity index calculation on benzene.
    Benzene (c1ccccc1) is the prototypical aromatic molecule.
    According to Hückel's rule (4n+2 pi electrons), benzene has 6 pi electrons (n=1).
    The aromaticity index should be non-zero and positive for aromatic systems.
    """
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, "Failed to parse benzene SMILES"

    # Calculate the aromaticity index
    # The implementation is expected to return a value > 0 for aromatic molecules
    aromaticity_index = compute_huckel_aromaticity_index(mol)

    # Assert that the index is a valid number
    assert isinstance(aromaticity_index, (int, float, np.floating)), \
        f"Aromaticity index should be numeric, got {type(aromaticity_index)}"

    # Assert that benzene has a positive aromaticity index (it is aromatic)
    # The exact value depends on the implementation details of the Hückel calculation
    # but it should be significantly greater than 0.
    # We use a small epsilon to account for floating point variations.
    assert aromaticity_index > 0.0, \
        f"Benzene should have a positive aromaticity index, got {aromaticity_index}"

def test_aromaticity_cyclobutadiene():
    """
    Test Hückel aromaticity index calculation on cyclobutadiene.
    Cyclobutadiene (C1=CC=C1) has 4 pi electrons (4n, n=1), making it anti-aromatic.
    The aromaticity index should be negative or significantly different from aromatic systems.
    """
    smiles = "C1=CC=C1"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, "Failed to parse cyclobutadiene SMILES"

    aromaticity_index = compute_huckel_aromaticity_index(mol)

    # Assert that the index is a valid number
    assert isinstance(aromaticity_index, (int, float, np.floating)), \
        f"Aromaticity index should be numeric, got {type(aromaticity_index)}"

    # Anti-aromatic molecules should have a negative or very low aromaticity index
    # depending on the specific formulation of the Hückel index used.
    # For this test, we expect it to be distinctly different from benzene.
    benzene_smiles = "c1ccccc1"
    benzene_mol = Chem.MolFromSmiles(benzene_smiles)
    benzene_index = compute_huckel_aromaticity_index(benzene_mol)

    assert aromaticity_index < benzene_index, \
        f"Cyclobutadiene ({aromaticity_index}) should have a lower aromaticity index than benzene ({benzene_index})"