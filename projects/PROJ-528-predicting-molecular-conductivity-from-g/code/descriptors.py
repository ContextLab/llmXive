"""
Descriptor computation module for molecular graph-based features.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdmolops
from rdkit.Chem.Scaffolds import MurckoScaffold

def get_bond_type_order(bond) -> float:
    """Get bond order from RDKit bond object."""
    bond_type = bond.GetBondType()
    if bond_type == Chem.BondType.SINGLE:
        return 1.0
    elif bond_type == Chem.BondType.DOUBLE:
        return 2.0
    elif bond_type == Chem.BondType.TRIPLE:
        return 3.0
    elif bond_type == Chem.BondType.AROMATIC:
        return 1.5  # Wikipedia: Bond order
    else:
        return 1.0

def get_atomic_number(atom) -> int:
    """Get atomic number from RDKit atom object."""
    return atom.GetAtomicNum()

def get_element_symbol(atom) -> str:
    """Get element symbol from RDKit atom object."""
    return atom.GetSymbol()

def estimate_bond_length(bond_type: float) -> float:
    """
    Estimate bond length based on bond type.
    Uses typical values: single=1.54, double=1.34, aromatic=1.39, triple=1.20 Angstroms.
    """
    if bond_type <= 1.0:
        return 1.54
    elif bond_type <= 1.5:
        return 1.39
    elif bond_type <= 2.0:
        return 1.34
    elif bond_type <= 3.0:
        return 1.20
    else:
        return 1.54

def identify_pi_system(mol: Chem.Mol) -> List[int]:
    """
    Identify atoms in the pi-system (conjugated system).
    
    Args:
        mol: RDKit molecule object
    
    Returns:
        List of atom indices in the pi-system
    """
    pi_atoms = []
    for atom in mol.GetAtoms():
        # Check if atom is part of a conjugated system
        if atom.GetIsConjugated() and atom.GetAtomicNum() in [6, 7, 8]:  # C, N, O
            pi_atoms.append(atom.GetIdx())
    return pi_atoms

def build_huckel_matrix(mol: Chem.Mol) -> np.ndarray:
    """
    Build Hückel Hamiltonian matrix for the pi-system.
    
    Args:
        mol: RDKit molecule object
    
    Returns:
        Hückel matrix (numpy array)
    """
    pi_atoms = identify_pi_system(mol)
    n = len(pi_atoms)
    
    if n == 0:
        return np.array([])
    
    # Initialize matrix with alpha = 0.0 (diagonal)
    H = np.zeros((n, n))
    
    # Set off-diagonal elements (beta = -1.0 for bonded atoms)
    atom_map = {idx: i for i, idx in enumerate(pi_atoms)}
    
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        
        if i in atom_map and j in atom_map:
            H[atom_map[i], atom_map[j]] = -1.0
            H[atom_map[j], atom_map[i]] = -1.0
    
    return H

def compute_huckel_resonance_energy(mol: Chem.Mol) -> float:
    """
    Compute Hückel resonance energy for the molecule.
    
    Args:
        mol: RDKit molecule object
    
    Returns:
        Resonance energy in kcal/mol (scaled by 200 kcal/mol per beta unit)
    """
    H = build_huckel_matrix(mol)
    
    if H.size == 0:
        return 0.0
    
    try:
        # Compute eigenvalues
        eigenvalues = np.linalg.eigvalsh(H)
        
        # Count pi-electrons (2 per pi-atom for simplicity)
        n_pi_atoms = len(H)
        n_electrons = n_pi_atoms * 2  # Simplified: 2 electrons per pi-atom
        
        # Fill orbitals (Aufbau principle: 2 electrons per orbital)
        occupied_eigenvalues = np.sort(eigenvalues)[:n_electrons // 2]
        total_delocalized_energy = np.sum(occupied_eigenvalues) * 2  # 2 electrons per orbital
        
        # Localized reference: each double bond contributes 1 beta unit
        # Count double bonds in pi-system
        n_double_bonds = 0
        for bond in mol.GetBonds():
            if bond.GetBondType() == Chem.BondType.DOUBLE:
                begin = bond.GetBeginAtomIdx()
                end = bond.GetEndAtomIdx()
                if begin in identify_pi_system(mol) and end in identify_pi_system(mol):
                    n_double_bonds += 1
        
        # Localized energy: n_double_bonds * 1 beta unit (each double bond = 1 beta)
        total_localized_energy = n_double_bonds * 1.0  # In beta units
        
        # Resonance energy = E_localized - E_delocalized
        resonance_energy_beta = total_localized_energy - total_delocalized_energy
        
        # Convert to kcal/mol (scaling factor: 200 kcal/mol per beta unit)
        resonance_energy_kcal = resonance_energy_beta * 200.0
        
        return float(resonance_energy_kcal)
        
    except Exception as e:
        logging.warning(f"Error computing Hückel resonance energy: {e}")
        return float('nan')

def compute_base_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """Compute base graph descriptors."""
    try:
        # Degree statistics
        degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
        degree_mean = np.mean(degrees) if degrees else 0.0
        degree_std = np.std(degrees) if degrees else 0.0
        degree_max = max(degrees) if degrees else 0.0
        degree_min = min(degrees) if degrees else 0.0
        
        # Path length statistics (using RDKit's GetDistanceMatrix)
        dist_matrix = rdMolDescriptors.GetDistanceMatrix(mol)
        path_lengths = dist_matrix[dist_matrix > 0].flatten()
        path_length_mean = np.mean(path_lengths) if len(path_lengths) > 0 else 0.0
        path_length_std = np.std(path_lengths) if len(path_lengths) > 0 else 0.0
        path_length_max = max(path_lengths) if len(path_lengths) > 0 else 0.0
        path_length_min = min(path_lengths) if len(path_lengths) > 0 else 0.0
        
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
        logging.warning(f"Error computing base descriptors: {e}")
        return {}

def compute_aromaticity(mol: Chem.Mol) -> Dict[str, float]:
    """Compute aromaticity descriptors."""
    try:
        aromatic_ring_count = rdMolDescriptors.CalcNumAromaticRings(mol)
        aromaticity_index = aromatic_ring_count / mol.GetNumRings() if mol.GetNumRings() > 0 else 0.0
        
        return {
            'aromaticity_index': aromaticity_index,
            'aromatic_ring_count': aromatic_ring_count
        }
    except Exception as e:
        logging.warning(f"Error computing aromaticity: {e}")
        return {}

def compute_conjugation(mol: Chem.Mol) -> Dict[str, float]:
    """Compute conjugation descriptors."""
    try:
        # Count conjugated bonds
        conjugated_bonds = sum(1 for bond in mol.GetBonds() if bond.GetIsConjugated())
        
        # Longest conjugated path (simplified: count of conjugated bonds)
        conjugation_length = conjugated_bonds
        
        # Conjugation density
        total_bonds = mol.GetNumBonds()
        conjugation_density = conjugated_bonds / total_bonds if total_bonds > 0 else 0.0
        
        return {
            'conjugation_length': conjugation_length,
            'num_conjugated_bonds': conjugated_bonds,
            'conjugation_density': conjugation_density
        }
    except Exception as e:
        logging.warning(f"Error computing conjugation: {e}")
        return {}

def compute_resonance_proxies(mol: Chem.Mol) -> Dict[str, float]:
    """Compute resonance proxies using RDKit."""
    try:
        aromatic_ring_count = rdMolDescriptors.CalcNumAromaticRings(mol)
        conjugated_ring_count = rdMolDescriptors.CalcNumConjugatedRings(mol) if hasattr(rdMolDescriptors, 'CalcNumConjugatedRings') else 0
        
        return {
            'aromatic_ring_count': aromatic_ring_count,
            'conjugated_ring_count': conjugated_ring_count
        }
    except Exception as e:
        logging.warning(f"Error computing resonance proxies: {e}")
        return {}

def compute_bond_order_weighted_path(mol: Chem.Mol) -> float:
    """
    Compute bond-order weighted path metric.
    Sum of (1 / estimated_bond_length) for the longest conjugated path.
    """
    try:
        pi_atoms = identify_pi_system(mol)
        if len(pi_atoms) < 2:
            return 0.0
        
        # Find longest path in conjugated subgraph
        max_path_length = 0
        total_weighted_length = 0.0
        
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            
            if i in pi_atoms and j in pi_atoms:
                bond_order = get_bond_type_order(bond)
                bond_length = estimate_bond_length(bond_order)
                weighted_length = 1.0 / bond_length
                total_weighted_length += weighted_length
                max_path_length = max(max_path_length, 1)
        
        return float(total_weighted_length) if max_path_length > 0 else 0.0
        
    except Exception as e:
        logging.warning(f"Error computing bond-order weighted path: {e}")
        return 0.0

def compute_electronegativity_polarity(mol: Chem.Mol) -> float:
    """
    Compute electronegativity-polarity score.
    Sum of (delta_EN * estimated_bond_length) across all bonds.
    """
    try:
        total_polarity = 0.0
        
        for bond in mol.GetBonds():
            atom1 = bond.GetBeginAtom()
            atom2 = bond.GetEndAtom()
            
            en1 = atom1.GetElectronegativity() if hasattr(atom1, 'GetElectronegativity') else 2.5
            en2 = atom2.GetElectronegativity() if hasattr(atom2, 'GetElectronegativity') else 2.5
            
            delta_en = abs(en1 - en2)
            bond_order = get_bond_type_order(bond)
            bond_length = estimate_bond_length(bond_order)
            
            polarity_contribution = delta_en * bond_length
            total_polarity += polarity_contribution
        
        return float(total_polarity)
        
    except Exception as e:
        logging.warning(f"Error computing electronegativity polarity: {e}")
        return 0.0

def compute_all_descriptors(smiles: str) -> Dict[str, Any]:
    """
    Compute all descriptors for a molecule from SMILES string.
    
    Args:
        smiles: SMILES string
    
    Returns:
        Dictionary of all descriptors
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {}
    
    descriptors = {}
    descriptors.update(compute_base_descriptors(mol))
    descriptors.update(compute_aromaticity(mol))
    descriptors.update(compute_conjugation(mol))
    descriptors.update(compute_resonance_proxies(mol))
    descriptors['bond_order_weighted_path'] = compute_bond_order_weighted_path(mol)
    descriptors['electronegativity_polarity_score'] = compute_electronegativity_polarity(mol)
    descriptors['huckel_resonance_energy'] = compute_huckel_resonance_energy(mol)
    
    return descriptors

def compute_descriptors_batch(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """
    Compute descriptors for a batch of molecules.
    
    Args:
        df: DataFrame with SMILES column
        smiles_col: Name of SMILES column
    
    Returns:
        DataFrame with descriptors added
    """
    all_descriptors = []
    
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        desc = compute_all_descriptors(smiles)
        desc['smiles'] = smiles
        all_descriptors.append(desc)
    
    return pd.DataFrame(all_descriptors)

# Wrapper functions for compatibility
def compute_base_descriptors_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    return compute_descriptors_batch(df)

def compute_aromaticity_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    return compute_descriptors_batch(df)

def compute_conjugation_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    return compute_descriptors_batch(df)

def compute_resonance_proxies_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    return compute_descriptors_batch(df)

def main():
    """Main entry point for descriptor computation."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    smiles_list = ['c1ccccc1', 'CC=CC=C', 'CCCC']
    for smiles in smiles_list:
        desc = compute_all_descriptors(smiles)
        print(f"SMILES: {smiles}")
        for k, v in desc.items():
            print(f"  {k}: {v}")

if __name__ == '__main__':
    main()
