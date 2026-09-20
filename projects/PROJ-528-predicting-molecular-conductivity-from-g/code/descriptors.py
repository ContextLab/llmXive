"""
Molecular descriptor computation module.
Computes graph-based, aromaticity, conjugation, resonance proxies, and Hückel resonance energy.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdmolops
from rdkit.Chem.rdchem import BondType

# Configure logging
logger = logging.getLogger(__name__)

# Bond type to order mapping
BOND_ORDER_MAP = {
    BondType.SINGLE: 1.0,
    BondType.DOUBLE: 2.0,
    BondType.TRIPLE: 3.0,
    BondType.AROMATIC: 1.5,
    BondType.UNSPECIFIED: 1.0
}

# Estimated bond lengths (Angstroms) for base single bonds
# Reference: typical values from literature
BASE_BOND_LENGTHS = {
    (6, 6): 1.54,   # C-C
    (6, 7): 1.47,   # C-N
    (6, 8): 1.43,   # C-O
    (6, 16): 1.82,  # C-S
    (7, 8): 1.40,   # N-O
    (7, 7): 1.45,   # N-N
    (8, 8): 1.48,   # O-O
    (6, 1): 1.09,   # C-H (approx)
    (1, 1): 0.74,   # H-H
    # Default fallback
    ('default'): 1.50
}

# Pauling electronegativities (approximate)
ELECTRONEGATIVITY = {
    1: 2.20,   # H
    6: 2.55,   # C
    7: 3.04,   # N
    8: 3.44,   # O
    9: 3.98,   # F
    15: 2.19,  # P
    16: 2.58,  # S
    17: 3.16,  # Cl
    # Add more as needed
}

def get_bond_type_order(bond_type: BondType) -> float:
    """Get the bond order from RDKit BondType."""
    return BOND_ORDER_MAP.get(bond_type, 1.0)

def get_atomic_number(atom) -> int:
    """Get atomic number from RDKit Atom object."""
    return atom.GetAtomicNum()

def get_element_symbol(atom) -> str:
    """Get element symbol from RDKit Atom object."""
    return atom.GetSymbol()

def estimate_bond_length(atom1, atom2, bond_order: float) -> float:
    """
    Estimate bond length based on atom types and bond order.
    Formula: length = base_length - (bond_order - 1) * 0.15
    """
    z1 = get_atomic_number(atom1)
    z2 = get_atomic_number(atom2)

    key = (min(z1, z2), max(z1, z2))
    base_length = BASE_BOND_LENGTHS.get(key, BASE_BOND_LENGTHS['default'])

    # Adjust for bond order
    estimated_length = base_length - (bond_order - 1.0) * 0.15
    return max(estimated_length, 0.5)  # Ensure positive length

def identify_pi_system(mol: Chem.Mol) -> List[int]:
    """
    Identify atoms in the conjugated pi-system.
    Returns list of atom indices that are part of the pi-system.
    """
    pi_atoms = []
    for atom in mol.GetAtoms():
        # Check if atom is sp2 or sp3 with lone pair participating in conjugation
        # Simplified: check for aromaticity or double/triple bonds
        if atom.GetIsAromatic():
            pi_atoms.append(atom.GetIdx())
        else:
            # Check for double/triple bonds
            for bond in atom.GetBonds():
                bt = bond.GetBondType()
                if bt == BondType.DOUBLE or bt == BondType.TRIPLE or bt == BondType.AROMATIC:
                    pi_atoms.append(atom.GetIdx())
                    break
    return list(set(pi_atoms))  # Unique indices

def build_huckel_matrix(mol: Chem.Mol) -> np.ndarray:
    """
    Build the Hückel Hamiltonian matrix for the pi-system.
    Diagonal (alpha) = 0.0, Off-diagonal (beta) = -1.0 for bonded pi-atoms.
    """
    pi_atoms = identify_pi_system(mol)
    n = len(pi_atoms)

    if n == 0:
        return np.array([]).reshape(0, 0)

    # Map atom index to matrix index
    atom_to_idx = {idx: i for i, idx in enumerate(pi_atoms)}
    H = np.zeros((n, n))

    # Set diagonal (alpha = 0.0)
    # H[i, i] = 0.0 (already zero)

    # Set off-diagonal (beta = -1.0 for bonded)
    for i, atom_idx in enumerate(pi_atoms):
        atom = mol.GetAtomWithIdx(atom_idx)
        for neighbor in atom.GetNeighbors():
            neighbor_idx = neighbor.GetIdx()
            if neighbor_idx in atom_to_idx:
                j = atom_to_idx[neighbor_idx]
                # Only set upper triangle to avoid double counting
                if i < j:
                    H[i, j] = -1.0
                    H[j, i] = -1.0

    return H

def compute_huckel_resonance_energy(mol: Chem.Mol) -> float:
    """
    Compute Hückel resonance energy for the molecule.
    1. Build Hückel matrix for pi-system.
    2. Compute eigenvalues (energy levels).
    3. Fill orbitals with pi-electrons (2 per orbital).
    4. Calculate Total Energy of delocalized system.
    5. Calculate Total Energy of localized reference (isolated C=C bonds).
    6. Resonance Energy = E_localized - E_delocalized.
    7. Convert to kcal/mol (scaling factor: 200 kcal/mol per beta unit).
    """
    H = build_huckel_matrix(mol)
    n = H.shape[0]

    if n == 0:
        return 0.0  # No pi-system

    # Compute eigenvalues
    eigenvalues = np.linalg.eigvalsh(H)  # Hermitian matrix, real eigenvalues

    # Count pi-electrons: 2 per pi-atom (simplified assumption for C-based systems)
    # More accurate: count based on atom type and bonding
    # For simplicity: assume each pi-atom contributes 1 pi-electron (e.g., C in aromatic ring)
    pi_electrons = n  # One per pi-atom

    # Fill orbitals (Aufbau principle, 2 electrons per orbital)
    # Sort eigenvalues ascending (lowest energy first)
    sorted_eigenvalues = np.sort(eigenvalues)
    num_occupied_orbitals = int(np.ceil(pi_electrons / 2))

    # Total energy of delocalized system
    # Sum of occupied orbital energies (each orbital holds 2 electrons, but energy is per orbital)
    # Actually: sum of (occupation * eigenvalue)
    # Occupation: 2 for full orbitals, 1 for half-filled (if odd electrons)
    e_delocalized = 0.0
    for i, ev in enumerate(sorted_eigenvalues):
        if i < num_occupied_orbitals - 1:
            e_delocalized += 2.0 * ev  # Full orbital
        elif i == num_occupied_orbitals - 1:
            # Last orbital: may be half-filled
            remaining_electrons = pi_electrons - 2 * (num_occupied_orbitals - 1)
            e_delocalized += remaining_electrons * ev

    # Localized reference: sum of isolated C=C double bond energies
    # Each C=C bond contributes 2 * beta (since 2 electrons in bonding orbital at energy beta)
    # Actually: in Hückel theory, isolated double bond has 2 electrons in orbital at energy beta.
    # So E_localized per double bond = 2 * beta = 2 * (-1.0) = -2.0
    # Number of double bonds = number of pi-electrons / 2
    num_double_bonds = pi_electrons / 2.0
    e_localized = num_double_bonds * 2.0 * (-1.0)  # 2 electrons per bond, energy beta=-1

    # Resonance energy (positive if delocalized is more stable)
    # RE = E_localized - E_delocalized
    resonance_energy_beta = e_localized - e_delocalized

    # Convert to kcal/mol (scaling factor: 200 kcal/mol per beta unit)
    resonance_energy_kcal = resonance_energy_beta * 200.0

    return resonance_energy_kcal

def compute_all_descriptors(smiles: str) -> Dict[str, Any]:
    """
    Compute all descriptors for a single SMILES string.
    Returns a dictionary with descriptor names and values.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {}

    desc = {}

    # Base graph descriptors
    desc.update(compute_base_descriptors(mol))

    # Aromaticity descriptors
    desc.update(compute_aromaticity(mol))

    # Conjugation descriptors
    desc.update(compute_conjugation(mol))

    # Resonance proxies
    desc.update(compute_resonance_proxies(mol))

    # Hückel resonance energy
    try:
        desc['huckel_resonance_energy'] = compute_huckel_resonance_energy(mol)
    except Exception as e:
        logger.warning(f"Failed to compute Hückel resonance energy for {smiles}: {e}")
        desc['huckel_resonance_energy'] = np.nan

    return desc

def compute_base_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """Compute base graph descriptors."""
    desc = {}

    # Degree statistics
    degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
    if degrees:
        desc['degree_mean'] = float(np.mean(degrees))
        desc['degree_std'] = float(np.std(degrees))
        desc['degree_max'] = float(np.max(degrees))
        desc['degree_min'] = float(np.min(degrees))
    else:
        desc['degree_mean'] = 0.0
        desc['degree_std'] = 0.0
        desc['degree_max'] = 0.0
        desc['degree_min'] = 0.0

    # Path length statistics (using RDKit's calcBondGraphDistance or similar)
    # Simplified: use average shortest path between atoms
    try:
        # Get all pairs shortest paths
        dist_matrix = rdmolops.GetDistanceMatrix(mol)
        # Filter out zero distances (same atom)
        paths = [dist_matrix[i, j] for i in range(len(dist_matrix)) for j in range(i+1, len(dist_matrix)) if dist_matrix[i, j] > 0]
        if paths:
            desc['path_length_mean'] = float(np.mean(paths))
            desc['path_length_std'] = float(np.std(paths))
            desc['path_length_max'] = float(np.max(paths))
            desc['path_length_min'] = float(np.min(paths))
        else:
            desc['path_length_mean'] = 0.0
            desc['path_length_std'] = 0.0
            desc['path_length_max'] = 0.0
            desc['path_length_min'] = 0.0
    except Exception as e:
        logger.warning(f"Failed to compute path length statistics: {e}")
        desc['path_length_mean'] = 0.0
        desc['path_length_std'] = 0.0
        desc['path_length_max'] = 0.0
        desc['path_length_min'] = 0.0

    return desc

def compute_aromaticity(mol: Chem.Mol) -> Dict[str, float]:
    """Compute aromaticity descriptors."""
    desc = {}

    # Aromaticity index (fraction of aromatic atoms)
    total_atoms = mol.GetNumAtoms()
    aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
    desc['aromaticity_index'] = float(aromatic_atoms / total_atoms) if total_atoms > 0 else 0.0

    return desc

def compute_ring_count(mol: Chem.Mol) -> Dict[str, int]:
    """Compute ring count descriptors."""
    desc = {}
    # Use RDKit's ring info
    ring_info = mol.GetRingInfo()
    desc['ring_count'] = ring_info.NumRings()
    return desc

def compute_conjugation(mol: Chem.Mol) -> Dict[str, float]:
    """Compute conjugation descriptors."""
    desc = {}

    # Identify conjugated bonds (double, triple, aromatic)
    conjugated_bonds = 0
    max_conjugation_path = 0

    # Simplified: count bonds with order > 1 or aromatic
    for bond in mol.GetBonds():
        bt = bond.GetBondType()
        if bt == BondType.DOUBLE or bt == BondType.TRIPLE or bt == BondType.AROMATIC:
            conjugated_bonds += 1

    desc['num_conjugated_bonds'] = conjugated_bonds

    # Conjugation length: longest path in conjugated subgraph
    # Simplified: use number of conjugated bonds as proxy
    desc['conjugation_length'] = float(conjugated_bonds)

    # Conjugation density: conjugated bonds / total bonds
    total_bonds = mol.GetNumBonds()
    desc['conjugation_density'] = float(conjugated_bonds / total_bonds) if total_bonds > 0 else 0.0

    return desc

def compute_resonance_proxies(mol: Chem.Mol) -> Dict[str, int]:
    """Compute resonance proxies using RDKit."""
    desc = {}

    # Aromatic ring count
    aromatic_ring_count = 0
    conjugated_ring_count = 0

    ring_info = mol.GetRingInfo()
    for ring in ring_info.AtomRings():
        is_aromatic = all(mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring)
        if is_aromatic:
            aromatic_ring_count += 1
            conjugated_ring_count += 1
        else:
            # Check if ring has conjugated bonds
            has_conjugation = False
            for i in range(len(ring)):
                bond = mol.GetBondBetweenAtoms(ring[i], ring[(i+1)%len(ring)])
                if bond:
                    bt = bond.GetBondType()
                    if bt == BondType.DOUBLE or bt == BondType.TRIPLE or bt == BondType.AROMATIC:
                        has_conjugation = True
                        break
            if has_conjugation:
                conjugated_ring_count += 1

    desc['aromatic_ring_count'] = aromatic_ring_count
    desc['conjugated_ring_count'] = conjugated_ring_count

    return desc

def compute_bond_order_weighted_path(mol: Chem.Mol) -> float:
    """
    Compute bond-order weighted path metric.
    Sum of (1 / estimated_bond_length) for the longest conjugated path.
    """
    # Identify conjugated path
    # Simplified: find longest path in the graph considering only conjugated bonds
    try:
        # Get all atoms
        atoms = list(mol.GetAtoms())
        n = len(atoms)

        if n == 0:
            return 0.0

        # Build adjacency list for conjugated bonds only
        adj = {i: [] for i in range(n)}
        bond_lengths = {}

        for bond in mol.GetBonds():
            bt = bond.GetBondType()
            if bt == BondType.DOUBLE or bt == BondType.TRIPLE or bt == BondType.AROMATIC:
                i = bond.GetBeginAtomIdx()
                j = bond.GetEndAtomIdx()
                order = get_bond_type_order(bt)
                length = estimate_bond_length(bond.GetBeginAtom(), bond.GetEndAtom(), order)
                adj[i].append(j)
                adj[j].append(i)
                bond_lengths[(min(i, j), max(i, j))] = length

        # Find longest simple path using DFS
        def dfs(node, visited):
            max_len = 0
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    # Edge weight: 1 / length
                    key = (min(node, neighbor), max(node, neighbor))
                    weight = 1.0 / bond_lengths.get(key, 1.5)
                    max_len = max(max_len, weight + dfs(neighbor, visited))
                    visited.remove(neighbor)
            return max_len

        max_weighted_path = 0.0
        for start in range(n):
            visited = {start}
            max_weighted_path = max(max_weighted_path, dfs(start, visited))

        return float(max_weighted_path)

    except Exception as e:
        logger.warning(f"Failed to compute bond-order weighted path: {e}")
        return 0.0

def compute_electronegativity_polarity(mol: Chem.Mol) -> float:
    """
    Compute electronegativity-polarity score.
    Sum of (delta_EN * estimated_bond_length) across all bonds.
    """
    total_polarity = 0.0

    for bond in mol.GetBonds():
        atom1 = bond.GetBeginAtom()
        atom2 = bond.GetEndAtom()
        z1 = get_atomic_number(atom1)
        z2 = get_atomic_number(atom2)

        en1 = ELECTRONEGATIVITY.get(z1, 2.55)  # Default to carbon
        en2 = ELECTRONEGATIVITY.get(z2, 2.55)

        delta_en = abs(en1 - en2)
        order = get_bond_type_order(bond.GetBondType())
        length = estimate_bond_length(atom1, atom2, order)

        total_polarity += delta_en * length

    return float(total_polarity)

def compute_aromatic_ring_count(mol: Chem.Mol) -> int:
    """Compute aromatic ring count."""
    return compute_resonance_proxies(mol)['aromatic_ring_count']

def compute_conjugated_ring_count(mol: Chem.Mol) -> int:
    """Compute conjugated ring count."""
    return compute_resonance_proxies(mol)['conjugated_ring_count']

def compute_descriptors_batch(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """
    Compute descriptors for a batch of SMILES strings.
    Returns a DataFrame with all descriptors.
    """
    all_desc = []

    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        try:
            desc = compute_all_descriptors(smiles)
            desc['smiles'] = smiles
            all_desc.append(desc)
        except Exception as e:
            logger.warning(f"Failed to compute descriptors for {smiles}: {e}")
            # Add row with NaN for all descriptors
            desc = {'smiles': smiles}
            # Get all possible keys from a successful computation (if any)
            if all_desc:
                for key in all_desc[0].keys():
                    if key != 'smiles':
                        desc[key] = np.nan
            all_desc.append(desc)

    return pd.DataFrame(all_desc)

# Wrapper functions for task compatibility
def compute_degree_statistics(mol: Chem.Mol) -> Dict[str, float]:
    return compute_base_descriptors(mol)

def compute_path_length_statistics(mol: Chem.Mol) -> Dict[str, float]:
    base = compute_base_descriptors(mol)
    return {k: v for k, v in base.items() if 'path_length' in k}

def compute_aromaticity_index(mol: Chem.Mol) -> float:
    return compute_aromaticity(mol)['aromaticity_index']

def compute_ring_count(mol: Chem.Mol) -> Dict[str, int]:
    return compute_ring_count(mol)

def compute_conjugation_length(mol: Chem.Mol) -> float:
    return compute_conjugation(mol)['conjugation_length']

def compute_num_conjugated_bonds(mol: Chem.Mol) -> int:
    return compute_conjugation(mol)['num_conjugated_bonds']

def compute_conjugation_density(mol: Chem.Mol) -> float:
    return compute_conjugation(mol)['conjugation_density']

def compute_aromatic_ring_count_wrapper(mol: Chem.Mol) -> int:
    return compute_aromatic_ring_count(mol)

def compute_conjugated_ring_count_wrapper(mol: Chem.Mol) -> int:
    return compute_conjugated_ring_count(mol)

def compute_bond_order_weighted_path_wrapper(mol: Chem.Mol) -> float:
    return compute_bond_order_weighted_path(mol)

def compute_electronegativity_polarity_wrapper(mol: Chem.Mol) -> float:
    return compute_electronegativity_polarity(mol)

# Note: The functions below are kept for backward compatibility with existing imports
# They call the appropriate internal functions
def compute_base_descriptors_wrapper(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """Wrapper for compute_all_descriptors to match existing API."""
    return compute_descriptors_batch(df, smiles_col)

def compute_aromaticity_wrapper(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """Wrapper to compute aromaticity descriptors."""
    desc_df = compute_descriptors_batch(df, smiles_col)
    return desc_df

def compute_conjugation_wrapper(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """Wrapper to compute conjugation descriptors."""
    desc_df = compute_descriptors_batch(df, smiles_col)
    return desc_df

def compute_resonance_proxies_wrapper(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """Wrapper to compute resonance proxy descriptors."""
    desc_df = compute_descriptors_batch(df, smiles_col)
    return desc_df