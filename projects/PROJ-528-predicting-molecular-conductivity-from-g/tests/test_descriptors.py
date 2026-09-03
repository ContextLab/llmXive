"""
Unit tests for descriptor calculations, focusing on conjugation path length
and mixed hybridization validation.
"""
import pytest
import numpy as np
from rdkit import Chem

from code.descriptors import compute_path_length_statistics, compute_degree_statistics


def get_conjugation_length(mol):
    """
    Calculate the length of the longest conjugated path in a molecule.
    A conjugated path is a sequence of alternating single and double bonds.
    Returns the number of bonds in the longest such path.
    """
    if mol is None:
        return 0

    # Build an adjacency list of conjugated bonds
    n_atoms = mol.GetNumAtoms()
    adj = {i: [] for i in range(n_atoms)}
    for bond in mol.GetBonds():
        if bond.GetIsConjugated():
            start = bond.GetBeginAtomIdx()
            end = bond.GetEndAtomIdx()
            adj[start].append(end)
            adj[end].append(start)

    # Find the longest path in this graph (DFS)
    max_len = 0

    def dfs(node, current_len, visited):
        nonlocal max_len
        if current_len > max_len:
            max_len = current_len

        for neighbor in adj[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                dfs(neighbor, current_len + 1, visited)
                visited.remove(neighbor)

    for start_node in range(n_atoms):
        if len(adj[start_node]) > 0:
            visited = {start_node}
            dfs(start_node, 0, visited)

    return max_len


def test_conjugation_path_length():
    """
    Test conjugation path length on butadiene vs. butane.
    Butadiene (C=CC=C) should have a longer conjugation path than butane (CCCC).
    """
    smiles_butadiene = "C=CC=C"
    smiles_butane = "CCCC"

    mol_butadiene = Chem.MolFromSmiles(smiles_butadiene)
    mol_butane = Chem.MolFromSmiles(smiles_butane)

    assert mol_butadiene is not None, f"Failed to parse SMILES: {smiles_butadiene}"
    assert mol_butane is not None, f"Failed to parse SMILES: {smiles_butane}"

    conjugation_length_butadiene = get_conjugation_length(mol_butadiene)
    conjugation_length_butane = get_conjugation_length(mol_butane)

    assert conjugation_length_butadiene > conjugation_length_butane, \
        f"Expected conjugation_length({smiles_butadiene}) > {smiles_butane}, " \
        f"got {conjugation_length_butadiene} vs {conjugation_length_butane}"


def test_mixed_hybridization_descriptors():
    """
    Test descriptor computation on mixed hybridization molecules.
    Uses a molecule with both sp2 and sp3 carbons (e.g., "CC=C").
    Asserts that all computed descriptors are finite numbers and no NaN values are present.
    """
    smiles_mixed = "CC=C"  # Propene: sp3 (CH3) and sp2 (CH=CH2)
    mol = Chem.MolFromSmiles(smiles_mixed)
    assert mol is not None, f"Failed to parse SMILES: {smiles_mixed}"

    # Compute degree statistics
    degree_stats = compute_degree_statistics(mol)

    # Compute path length statistics
    path_stats = compute_path_length_statistics(mol)

    # Collect all descriptor values
    descriptors = list(degree_stats.values()) + list(path_stats.values())

    # Assert all values are finite (not NaN, not Inf)
    for val in descriptors:
        assert np.isfinite(val), f"Descriptor value is not finite: {val}"

    # Assert no NaN values explicitly (redundant with isfinite but explicit for clarity)
    assert not any(np.isnan(v) for v in descriptors), "Found NaN values in computed descriptors"