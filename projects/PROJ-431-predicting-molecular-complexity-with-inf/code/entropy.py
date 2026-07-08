"""
Entropy module for computing information-theoretic complexity scores of molecules.

This module implements Shannon entropy calculations based on:
- Atom degree distribution (topological connectivity)
- Bond degree distribution (connectivity of bonds)

CRITICAL DEFINITION (FR-002, FR-003):
The term "entropy" in this module refers specifically to the **Shannon entropy**
of discrete degree distributions derived from the molecular graph topology.

- **Structural Information**: The distribution of atom degrees (number of non-hydrogen
  neighbors) and bond degrees (sum of connected atom degrees).
- **Mathematical Formulation**: H = -Σ p(x) log₂ p(x), where p(x) is the probability
  mass function of a specific degree value occurring in the graph.

This metric quantifies the *topological diversity* of the molecular structure.
It is distinct from:
- Mutual Information (which measures dependency between variables)
- Algorithmic Complexity/Kolmogorov Complexity (which measures the shortest description length)

We choose Shannon degree entropy because it directly captures the heterogeneity
of local connectivity patterns, which serves as a proxy for structural complexity
relevant to physicochemical properties like solubility and permeability.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

logger = logging.getLogger(__name__)


def compute_atom_entropy(smiles: str) -> Optional[float]:
    """
    Compute the Shannon entropy of atom degree distribution for a molecule.

    **Definition**: This calculates the Shannon entropy of the distribution of
    atom degrees (number of non-hydrogen neighbors) in the molecular graph.
    
    *Formal Context*: This is a measure of the topological structural information
    content. It quantifies how diverse the local connectivity environments are
    within the molecule. A molecule with all atoms having the same degree (e.g.,
    benzene) has low entropy (0.0), while a molecule with highly varied connectivity
    has higher entropy.

    Args:
        smiles: SMILES string representation of the molecule.

    Returns:
        Shannon entropy value (float) if the molecule is valid, None otherwise.
        Returns 0.0 for molecules with only one unique degree value (no variation).

    Raises:
        None: Returns None for invalid SMILES or molecules with no atoms.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Invalid SMILES string: {smiles}")
        return None

    # Get atom degrees (non-hydrogen neighbors)
    degrees = []
    for atom in mol.GetAtoms():
        degree = atom.GetDegree()
        degrees.append(degree)

    if not degrees:
        logger.warning(f"Molecule has no atoms: {smiles}")
        return None

    # Calculate frequency distribution of degrees
    degree_counts = {}
    for deg in degrees:
        degree_counts[deg] = degree_counts.get(deg, 0) + 1

    total_atoms = len(degrees)

    # Calculate Shannon entropy: H = -Σ p(x) log₂ p(x)
    entropy = 0.0
    for count in degree_counts.values():
        p = count / total_atoms
        if p > 0:
            entropy -= p * np.log2(p)

    return entropy


def compute_bond_entropy(smiles: str) -> Optional[float]:
    """
    Compute the Shannon entropy of bond degree distribution for a molecule.

    **Definition**: This calculates the Shannon entropy of the distribution of
    bond degrees. The bond degree is defined as the sum of the degrees of the
    two atoms connected by the bond.
    
    *Formal Context*: This captures the diversity of bond connectivity patterns.
    It reflects the structural information content regarding how atoms are
    interconnected. High variance in bond degrees indicates a complex, heterogeneous
    connectivity structure.

    Args:
        smiles: SMILES string representation of the molecule.

    Returns:
        Shannon entropy value (float) if the molecule is valid, None otherwise.
        Returns 0.0 for molecules with only one unique bond degree value.

    Raises:
        None: Returns None for invalid SMILES or molecules with no bonds.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Invalid SMILES string: {smiles}")
        return None

    # Get bond degrees (sum of atom degrees for connected atoms)
    bond_degrees = []
    for bond in mol.GetBonds():
        atom1_deg = bond.GetBeginAtom().GetDegree()
        atom2_deg = bond.GetEndAtom().GetDegree()
        bond_degree = atom1_deg + atom2_deg
        bond_degrees.append(bond_degree)

    if not bond_degrees:
        logger.warning(f"Molecule has no bonds: {smiles}")
        return None

    # Calculate frequency distribution of bond degrees
    bond_degree_counts = {}
    for deg in bond_degrees:
        bond_degree_counts[deg] = bond_degree_counts.get(deg, 0) + 1

    total_bonds = len(bond_degrees)

    # Calculate Shannon entropy: H = -Σ p(x) log₂ p(x)
    entropy = 0.0
    for count in bond_degree_counts.values():
        p = count / total_bonds
        if p > 0:
            entropy -= p * np.log2(p)

    return entropy


def compute_entropy_for_dataframe(smiles_list: List[str]) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """
    Compute atom and bond entropy for a list of SMILES strings.

    This is a convenience function for batch processing.

    Args:
        smiles_list: List of SMILES strings.

    Returns:
        Tuple of (atom_entropies, bond_entropies) lists, where each element
        is either a float or None (for invalid SMILES).
    """
    atom_entropies = []
    bond_entropies = []

    for smiles in smiles_list:
        atom_ent = compute_atom_entropy(smiles)
        bond_ent = compute_bond_entropy(smiles)
        atom_entropies.append(atom_ent)
        bond_entropies.append(bond_ent)

    return atom_entropies, bond_entropies