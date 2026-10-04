"""
Descriptor Computation Module (T014a-d)

Functions:
- compute_base_descriptors (T014a)
- compute_aromaticity (T014b)
- compute_conjugation (T014c)
- compute_resonance_proxies (T014d)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdmolops
from rdkit.Chem.Scaffolds import MurckoScaffold
import time

logger = logging.getLogger(__name__)

# Configuration for runtime monitoring (FR-010)
COMPUTE_TIMEOUT_SECONDS = 5.0  # Warning threshold per molecule

def get_bond_type_order(bond) -> float:
    """Get bond order (1, 2, 3, 1.5 for aromatic)."""
    if bond.GetIsAromatic():
        return 1.5
    return float(bond.GetBondTypeAsDouble())

def get_atomic_number(atom) -> int:
    """Get atomic number."""
    return atom.GetAtomicNum()

def get_element_symbol(atom) -> str:
    """Get element symbol."""
    return atom.GetSymbol()

def estimate_bond_length(bond) -> float:
    """Estimate bond length based on bond type and atoms."""
    # Simplified estimation
    order = get_bond_type_order(bond)
    if order >= 3:
        return 1.20
    elif order >= 2:
        return 1.34
    elif order >= 1.5:
        return 1.39
    else:
        return 1.54

def identify_pi_system(mol: Chem.Mol) -> List[int]:
    """Identify atoms in pi systems (conjugated/aromatic)."""
    pi_atoms = []
    for atom in mol.GetAtoms():
        if atom.GetIsAromatic() or atom.GetHybridization() == Chem.HybridizationType.SP2:
            pi_atoms.append(atom.GetIdx())
    return pi_atoms

def build_huckel_matrix(mol: Chem.Mol) -> np.ndarray:
    """Build Hückel matrix for a molecule."""
    # Placeholder for Hückel matrix construction
    n = mol.GetNumAtoms()
    H = np.zeros((n, n))
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        H[i, j] = H[j, i] = -1.0  # Beta
    # Alpha on diagonal (0.0 relative)
    return H

def compute_huckel_resonance_energy(mol: Chem.Mol) -> float:
    """Compute Hückel resonance energy."""
    H = build_huckel_matrix(mol)
    eigenvalues = np.linalg.eigvalsh(H)
    # Simple approximation: sum of occupied orbital energies
    # Assuming 2 electrons per orbital, fill lowest half
    n_electrons = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic()) * 1  # Simplified
    n_orbitals = len(eigenvalues)
    occupied = sorted(eigenvalues)[:n_electrons//2]
    return float(np.sum(occupied))

def compute_base_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    T014a: Compute base graph descriptors.
    Columns: degree_mean, degree_std, degree_max, degree_min,
             path_length_mean, path_length_std, path_length_max, path_length_min
    """
    def compute_for_molecule(smiles: str) -> Dict[str, float]:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {
                    'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan,
                    'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan
                }

            # Degree (connectivity)
            degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
            if not degrees:
                return {
                    'degree_mean': 0.0, 'degree_std': 0.0, 'degree_max': 0.0, 'degree_min': 0.0,
                    'path_length_mean': 0.0, 'path_length_std': 0.0, 'path_length_max': 0.0, 'path_length_min': 0.0
                }

            degree_mean = float(np.mean(degrees))
            degree_std = float(np.std(degrees))
            degree_max = float(np.max(degrees))
            degree_min = float(np.min(degrees))

            # Path lengths (shortest paths between all pairs)
            # Using RDKit's GetDistanceMatrix
            dist_matrix = rdMolDescriptors.GetDistanceMatrix(mol)
            # Flatten and filter out zeros (self-distances) and infinities
            paths = []
            n = len(dist_matrix)
            for i in range(n):
                for j in range(i + 1, n):
                    d = dist_matrix[i, j]
                    if d > 0 and not np.isinf(d):
                        paths.append(d)

            if not paths:
                return {
                    'degree_mean': degree_mean, 'degree_std': degree_std, 'degree_max': degree_max, 'degree_min': degree_min,
                    'path_length_mean': 0.0, 'path_length_std': 0.0, 'path_length_max': 0.0, 'path_length_min': 0.0
                }

            path_length_mean = float(np.mean(paths))
            path_length_std = float(np.std(paths))
            path_length_max = float(np.max(paths))
            path_length_min = float(np.min(paths))

            return {
                'degree_mean': degree_mean,
                'degree_std': degree_std,
                'degree_max': degree_max,
                'degree_min': degree_min,
                'path_length_mean': path_length_mean,
                'path_length_std': path_length_std,
                'path_length_max': path_length_max,
                'path_length_min': path_length_min
            }
        except Exception as e:
            logger.warning(f"Error computing base descriptors for SMILES '{smiles}': {e}")
            return {
                'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan,
                'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan
            }

    results = df['smiles'].apply(compute_for_molecule)
    # Convert list of dicts to DataFrame
    df_descriptors = pd.DataFrame(results.tolist(), index=df.index)
    return pd.concat([df, df_descriptors], axis=1)

def compute_aromaticity(df: pd.DataFrame) -> pd.DataFrame:
    """
    T014b: Compute aromaticity and ring descriptors.
    Columns: aromaticity_index, ring_count
    """
    def compute_for_molecule(smiles: str) -> Dict[str, float]:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {'aromaticity_index': np.nan, 'ring_count': np.nan}

            # Ring count
            ring_info = mol.GetRingInfo()
            ring_count = float(ring_info.NumRings())

            # Aromaticity index (simplified: ratio of aromatic atoms to total atoms)
            total_atoms = mol.GetNumAtoms()
            if total_atoms == 0:
                aromaticity_index = 0.0
            else:
                aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
                aromaticity_index = float(aromatic_atoms / total_atoms)

            return {
                'aromaticity_index': aromaticity_index,
                'ring_count': ring_count
            }
        except Exception as e:
            logger.warning(f"Error computing aromaticity for SMILES '{smiles}': {e}")
            return {'aromaticity_index': np.nan, 'ring_count': np.nan}

    results = df['smiles'].apply(compute_for_molecule)
    df_descriptors = pd.DataFrame(results.tolist(), index=df.index)
    return pd.concat([df, df_descriptors], axis=1)

def compute_conjugation(df: pd.DataFrame) -> pd.DataFrame:
    """
    T014c: Compute conjugation descriptors.
    Columns: conjugation_length, num_conjugated_bonds, conjugation_density
    """
    def compute_for_molecule(smiles: str) -> Dict[str, float]:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {'conjugation_length': np.nan, 'num_conjugated_bonds': np.nan, 'conjugation_density': np.nan}

            # Identify conjugated bonds (alternating single/double/aromatic)
            # A simple heuristic: count bonds between sp2 or aromatic atoms
            conjugated_bonds = 0
            for bond in mol.GetBonds():
                begin_atom = bond.GetBeginAtom()
                end_atom = bond.GetEndAtom()
                if (begin_atom.GetIsAromatic() or begin_atom.GetHybridization() == Chem.HybridizationType.SP2) and \
                   (end_atom.GetIsAromatic() or end_atom.GetHybridization() == Chem.HybridizationType.SP2):
                    conjugated_bonds += 1

            # Conjugation length: longest simple path in the conjugated subgraph
            # This is computationally expensive, so we use a simplified metric:
            # Number of conjugated bonds
            conjugation_length = float(conjugated_bonds)

            # Conjugation density: ratio of conjugated bonds to total bonds
            total_bonds = mol.GetNumBonds()
            if total_bonds == 0:
                conjugation_density = 0.0
            else:
                conjugation_density = float(conjugated_bonds / total_bonds)

            return {
                'conjugation_length': conjugation_length,
                'num_conjugated_bonds': float(conjugated_bonds),
                'conjugation_density': conjugation_density
            }
        except Exception as e:
            logger.warning(f"Error computing conjugation for SMILES '{smiles}': {e}")
            return {'conjugation_length': np.nan, 'num_conjugated_bonds': np.nan, 'conjugation_density': np.nan}

    results = df['smiles'].apply(compute_for_molecule)
    df_descriptors = pd.DataFrame(results.tolist(), index=df.index)
    return pd.concat([df, df_descriptors], axis=1)

def compute_resonance_proxies(df: pd.DataFrame) -> pd.DataFrame:
    """
    T014d: Compute resonance proxies (RDKit Only).
    Columns: aromatic_ring_count, conjugated_ring_count
    """
    def compute_for_molecule(smiles: str) -> Dict[str, float]:
        start_time = time.time()
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {'aromatic_ring_count': np.nan, 'conjugated_ring_count': np.nan}

            # Aromatic ring count
            aromatic_ring_count = float(rdMolDescriptors.CalcNumAromaticRings(mol))

            # Conjugated ring count (rings with conjugated bonds)
            # RDKit doesn't have a direct function, so we approximate:
            # Count rings that have at least one aromatic bond
            ring_info = mol.GetRingInfo()
            conjugated_ring_count = 0
            for ring in ring_info.AtomRings():
                # Check if any bond in the ring is aromatic
                has_aromatic = False
                for i in range(len(ring)):
                    atom1_idx = ring[i]
                    atom2_idx = ring[(i + 1) % len(ring)]
                    bond = mol.GetBondBetweenAtoms(atom1_idx, atom2_idx)
                    if bond and bond.GetIsAromatic():
                        has_aromatic = True
                        break
                if has_aromatic:
                    conjugated_ring_count += 1

            # Runtime monitoring (FR-010)
            elapsed = time.time() - start_time
            if elapsed > COMPUTE_TIMEOUT_SECONDS:
                logger.warning(f"Descriptor computation for '{smiles}' took {elapsed:.2f}s (threshold: {COMPUTE_TIMEOUT_SECONDS}s)")

            return {
                'aromatic_ring_count': aromatic_ring_count,
                'conjugated_ring_count': float(conjugated_ring_count)
            }
        except Exception as e:
            logger.warning(f"Error computing resonance proxies for SMILES '{smiles}': {e}")
            return {'aromatic_ring_count': np.nan, 'conjugated_ring_count': np.nan}

    results = df['smiles'].apply(compute_for_molecule)
    df_descriptors = pd.DataFrame(results.tolist(), index=df.index)
    return pd.concat([df, df_descriptors], axis=1)

def compute_all_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all descriptor sets."""
    df = compute_base_descriptors(df)
    df = compute_aromaticity(df)
    df = compute_conjugation(df)
    df = compute_resonance_proxies(df)
    return df

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """Compute descriptors for a list of SMILES strings."""
    df = pd.DataFrame({'smiles': smiles_list})
    return compute_all_descriptors(df)

def main():
    """CLI for testing descriptor computation."""
    import argparse
    parser = argparse.ArgumentParser(description="Test descriptor computation.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV with SMILES.")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path.")
    args = parser.parse_args()

    from code.logging_config import setup_logging
    setup_logging()

    df = pd.read_csv(args.input)
    if 'smiles' not in df.columns:
        logger.error("Input file must contain 'smiles' column.")
        return 1

    logger.info("Computing descriptors...")
    df_desc = compute_all_descriptors(df)
    df_desc.to_csv(args.output, index=False)
    logger.info(f"Saved descriptors to {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
