import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem import Descriptors

logger = logging.getLogger(__name__)

# Constants for fallback logic
DEFAULT_CONJUGATION_LENGTH = 0.0
DEFAULT_HUCKEL_INDEX = 0.0
DEFAULT_BOND_POLARITY = 0.0
DEFAULT_RESONANCE_ENERGY = 0.0

def compute_degree_statistics(mol: Chem.Mol) -> Tuple[float, float, float, float]:
    """Compute mean, std, max, min of atom degrees."""
    if mol is None:
        return 0.0, 0.0, 0.0, 0.0
    degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
    if not degrees:
        return 0.0, 0.0, 0.0, 0.0
    return float(np.mean(degrees)), float(np.std(degrees)), float(np.max(degrees)), float(np.min(degrees))

def compute_path_length_statistics(mol: Chem.Mol) -> Tuple[float, float, float, float]:
    """Compute mean, std, max, min of path lengths (topological distance)."""
    if mol is None:
        return 0.0, 0.0, 0.0, 0.0
    try:
        dists = rdMolDescriptors.GetDistanceMatrix(mol)
        # Flatten and filter out zeros (self-distances) and infinities
        flat_dists = [d for d in dists.flatten() if d > 0 and not np.isinf(d)]
        if not flat_dists:
            return 0.0, 0.0, 0.0, 0.0
        return float(np.mean(flat_dists)), float(np.std(flat_dists)), float(np.max(flat_dists)), float(np.min(flat_dists))
    except Exception:
        return 0.0, 0.0, 0.0, 0.0

def compute_ring_count(mol: Chem.Mol) -> int:
    """Count the number of rings in the molecule."""
    if mol is None:
        return 0
    return mol.GetRingInfo().NumRings()

def compute_huckel_aromaticity_index(mol: Chem.Mol) -> float:
    """
    Compute a Hückel aromaticity index based on the presence of aromatic rings.
    Returns 1.0 if the molecule has at least one aromatic ring, else 0.0.
    """
    if mol is None:
        return DEFAULT_HUCKEL_INDEX
    try:
        # RDKit's aromaticity detection
        if mol.GetNumAromaticRings() > 0:
            return 1.0
        return 0.0
    except Exception:
        logger.warning("Failed to compute aromaticity index, using fallback 0.0")
        return DEFAULT_HUCKEL_INDEX

def compute_aromatic_ring_count(mol: Chem.Mol) -> int:
    """Count the number of aromatic rings."""
    if mol is None:
        return 0
    try:
        return mol.GetNumAromaticRings()
    except Exception:
        logger.warning("Failed to count aromatic rings, using fallback 0")
        return 0

def compute_bond_order_annotation(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Estimate bond orders and assign effective bond lengths based on hybridization.
    Returns a dict with 'sp2_count', 'sp3_count', 'aromatic_bond_count'.
    """
    if mol is None:
        return {'sp2_count': 0, 'sp3_count': 0, 'aromatic_bond_count': 0}
    
    sp2_count = 0
    sp3_count = 0
    aromatic_bond_count = 0

    for bond in mol.GetBonds():
        bond_type = bond.GetBondType()
        if bond.GetIsAromatic():
            aromatic_bond_count += 1
        else:
            if bond_type == Chem.BondType.DOUBLE:
                sp2_count += 1
            elif bond_type == Chem.BondType.SINGLE:
                # Check atom hybridization to distinguish sp2-sp3 single bonds
                atom1 = bond.GetBeginAtom()
                atom2 = bond.GetEndAtom()
                if atom1.GetHybridization() == Chem.HybridizationType.SP2 or \
                   atom2.GetHybridization() == Chem.HybridizationType.SP2:
                    sp2_count += 1
                else:
                    sp3_count += 1
    
    return {'sp2_count': sp2_count, 'sp3_count': sp3_count, 'aromatic_bond_count': aromatic_bond_count}

def compute_bond_polarity(mol: Chem.Mol) -> float:
    """
    Calculate electronegativity difference weighted by bond length.
    Uses Pauling scale values from RDKit.
    """
    if mol is None:
        return DEFAULT_BOND_POLARITY
    
    total_polarity = 0.0
    count = 0
    
    # Pauling electronegativity values (simplified for common elements)
    electronegativity = {
        'H': 2.20, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98,
        'Cl': 3.16, 'Br': 2.96, 'I': 2.66, 'S': 2.58, 'P': 2.19
    }
    
    # Effective bond lengths (Angstroms)
    bond_lengths = {
        Chem.BondType.SINGLE: 1.54,
        Chem.BondType.DOUBLE: 1.34,
        Chem.BondType.TRIPLE: 1.20,
        Chem.BondType.AROMATIC: 1.39
    }

    for bond in mol.GetBonds():
        atom1 = bond.GetBeginAtom()
        atom2 = bond.GetEndAtom()
        sym1 = atom1.GetSymbol()
        sym2 = atom2.GetSymbol()
        
        en1 = electronegativity.get(sym1, 2.55)
        en2 = electronegativity.get(sym2, 2.55)
        
        diff = abs(en1 - en2)
        
        bond_type = bond.GetBondType()
        length = bond_lengths.get(bond_type, 1.54)
        
        # If aromatic, use aromatic length
        if bond.GetIsAromatic():
            length = 1.39
        
        total_polarity += diff * length
        count += 1
    
    if count == 0:
        return DEFAULT_BOND_POLARITY
    
    return float(total_polarity / count)

def compute_resonance_energy(mol: Chem.Mol) -> float:
    """
    Estimate resonance energy using Hückel Molecular Orbital (HMO) theory approximations.
    Simplified: E_res ~ 0.5 * pi_electrons * beta (where beta is resonance integral).
    Returns a scalar estimate in arbitrary units proportional to beta.
    """
    if mol is None:
        return DEFAULT_RESONANCE_ENERGY
    
    try:
        # Count pi electrons based on aromaticity and conjugation
        pi_electrons = 0
        
        for atom in mol.GetAtoms():
            if atom.GetIsAromatic():
                # Assume 1 pi electron for aromatic carbon-like atoms
                if atom.GetSymbol() == 'C':
                    pi_electrons += 1
                elif atom.GetSymbol() in ['N', 'O']:
                    # Nitrogen/Oxygen in aromatic rings contribute 1 or 2 depending on hybridization
                    # Simplified: assume 1 for now
                    pi_electrons += 1
        
        # Hückel resonance energy approximation: E_res = k * pi_electrons
        # Using a simplified constant k=0.5 (arbitrary units)
        return float(0.5 * pi_electrons)
    except Exception:
        logger.warning("Failed to compute resonance energy, using fallback 0.0")
        return DEFAULT_RESONANCE_ENERGY

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """
    Compute all descriptors for a batch of SMILES strings.
    Implements fallback logic for missing quantum descriptors (FR-014).
    """
    results = []
    
    for smiles in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                results.append({
                    'smiles': smiles,
                    'status': 'invalid',
                    'degree_mean': 0.0, 'degree_std': 0.0, 'degree_max': 0.0, 'degree_min': 0.0,
                    'path_length_mean': 0.0, 'path_length_std': 0.0, 'path_length_max': 0.0, 'path_length_min': 0.0,
                    'aromaticity_index': DEFAULT_HUCKEL_INDEX,
                    'conjugation_length': DEFAULT_CONJUGATION_LENGTH,
                    'ring_count': 0,
                    'bond_polarity': DEFAULT_BOND_POLARITY,
                    'resonance_energy': DEFAULT_RESONANCE_ENERGY
                })
                continue
            
            # Standard descriptors
            deg_mean, deg_std, deg_max, deg_min = compute_degree_statistics(mol)
            path_mean, path_std, path_max, path_min = compute_path_length_statistics(mol)
            ring_cnt = compute_ring_count(mol)
            
            # Quantum-inspired proxies
            huckel_idx = compute_huckel_aromaticity_index(mol)
            aromatic_rings = compute_aromatic_ring_count(mol)
            bond_order_info = compute_bond_order_annotation(mol)
            bond_pol = compute_bond_polarity(mol)
            res_energy = compute_resonance_energy(mol)
            
            # Conjugation length: sum of sp2 and aromatic bonds as proxy
            conj_len = float(bond_order_info['sp2_count'] + bond_order_info['aromatic_bond_count'])
            
            results.append({
                'smiles': smiles,
                'status': 'valid',
                'degree_mean': deg_mean, 'degree_std': deg_std, 'degree_max': deg_max, 'degree_min': deg_min,
                'path_length_mean': path_mean, 'path_length_std': path_std, 'path_length_max': path_max, 'path_length_min': path_min,
                'aromaticity_index': huckel_idx,
                'conjugation_length': conj_len,
                'ring_count': ring_cnt,
                'bond_polarity': bond_pol,
                'resonance_energy': res_energy
            })
            
        except Exception as e:
            logger.warning(f"Error processing {smiles}: {str(e)}. Using fallback values.")
            # Fallback for any error
            results.append({
                'smiles': smiles,
                'status': 'error',
                'degree_mean': 0.0, 'degree_std': 0.0, 'degree_max': 0.0, 'degree_min': 0.0,
                'path_length_mean': 0.0, 'path_length_std': 0.0, 'path_length_max': 0.0, 'path_length_min': 0.0,
                'aromaticity_index': DEFAULT_HUCKEL_INDEX,
                'conjugation_length': DEFAULT_CONJUGATION_LENGTH,
                'ring_count': 0,
                'bond_polarity': DEFAULT_BOND_POLARITY,
                'resonance_energy': DEFAULT_RESONANCE_ENERGY
            })
    
    return pd.DataFrame(results)

def compute_standard_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """
    Compute standard topological descriptors with fallback logic.
    Returns a dictionary of descriptor names and values.
    """
    if mol is None:
        logger.warning("Molecule is None, returning fallback standard descriptors")
        return {
            'degree_mean': 0.0, 'degree_std': 0.0, 'degree_max': 0.0, 'degree_min': 0.0,
            'path_length_mean': 0.0, 'path_length_std': 0.0, 'path_length_max': 0.0, 'path_length_min': 0.0,
            'ring_count': 0
        }
    
    try:
        deg_mean, deg_std, deg_max, deg_min = compute_degree_statistics(mol)
        path_mean, path_std, path_max, path_min = compute_path_length_statistics(mol)
        ring_cnt = compute_ring_count(mol)
        
        return {
            'degree_mean': deg_mean, 'degree_std': deg_std, 'degree_max': deg_max, 'degree_min': deg_min,
            'path_length_mean': path_mean, 'path_length_std': path_std, 'path_length_max': path_max, 'path_length_min': path_min,
            'ring_count': float(ring_cnt)
        }
    except Exception as e:
        logger.warning(f"Error computing standard descriptors: {str(e)}. Using fallback values.")
        return {
            'degree_mean': 0.0, 'degree_std': 0.0, 'degree_max': 0.0, 'degree_min': 0.0,
            'path_length_mean': 0.0, 'path_length_std': 0.0, 'path_length_max': 0.0, 'path_length_min': 0.0,
            'ring_count': 0.0
        }