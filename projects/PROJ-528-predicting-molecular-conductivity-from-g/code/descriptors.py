import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem import Descriptors
from rdkit.Chem import rdchem

logger = logging.getLogger(__name__)

# Constants for electronegativity (Pauling scale)
# Approximate values for common atoms in organic molecules
ELECTRONEGATIVITY = {
    6: 2.55,  # C
    1: 2.20,  # H
    7: 3.04,  # N
    8: 3.44,  # O
    16: 2.58, # S
    15: 2.19, # P
    9: 3.98,  # F
    17: 3.16, # Cl
    35: 2.96, # Br
    53: 2.66, # I
}

# Bond lengths (Angstroms)
BOND_LENGTHS = {
    'SINGLE': 1.54,
    'DOUBLE': 1.34,
    'TRIPLE': 1.20,
    'AROMATIC': 1.39,
}

def compute_degree_statistics(mol: Chem.Mol) -> Dict[str, float]:
    """Compute mean, std, max, min of atom degrees."""
    if mol is None:
        return {'mean': 0.0, 'std': 0.0, 'max': 0.0, 'min': 0.0}
    
    degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
    if not degrees:
        return {'mean': 0.0, 'std': 0.0, 'max': 0.0, 'min': 0.0}
    
    return {
        'mean': float(np.mean(degrees)),
        'std': float(np.std(degrees)),
        'max': float(np.max(degrees)),
        'min': float(np.min(degrees))
    }

def compute_path_length_statistics(mol: Chem.Mol) -> Dict[str, float]:
    """Compute mean, std, max, min of shortest path lengths between all pairs."""
    if mol is None:
        return {'mean': 0.0, 'std': 0.0, 'max': 0.0, 'min': 0.0}
    
    # Use RDKit's GetDistanceMatrix
    try:
        dist_matrix = rdMolDescriptors.GetDistanceMatrix(mol)
        # Flatten and filter out self-distances (0) and disconnected components (inf)
        paths = []
        for i in range(len(dist_matrix)):
            for j in range(i + 1, len(dist_matrix)):
                d = dist_matrix[i, j]
                if d != 0 and d != float('inf'):
                    paths.append(d)
        
        if not paths:
            return {'mean': 0.0, 'std': 0.0, 'max': 0.0, 'min': 0.0}
        
        return {
            'mean': float(np.mean(paths)),
            'std': float(np.std(paths)),
            'max': float(np.max(paths)),
            'min': float(np.min(paths))
        }
    except Exception as e:
        logger.warning(f"Error computing path length statistics: {e}")
        return {'mean': 0.0, 'std': 0.0, 'max': 0.0, 'min': 0.0}

def compute_ring_count(mol: Chem.Mol) -> int:
    """Count the number of rings in the molecule."""
    if mol is None:
        return 0
    try:
        return mol.GetRingInfo().NumRings()
    except Exception as e:
        logger.warning(f"Error computing ring count: {e}")
        return 0

def compute_huckel_aromaticity_index(mol: Chem.Mol) -> float:
    """
    Compute a Hückel aromaticity index.
    Heuristic: Count aromatic rings and weight by size (4n+2 rule approximation).
    Returns a normalized score.
    """
    if mol is None:
        return 0.0
    
    try:
        # Use RDKit's aromaticity detection
        aromatic_rings = []
        ring_info = mol.GetRingInfo()
        for ring in ring_info.AtomRings():
            # Check if all atoms in the ring are aromatic
            if all(mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring):
                aromatic_rings.append(ring)
        
        if not aromatic_rings:
            return 0.0
        
        # Simple heuristic: count aromatic rings weighted by conjugation potential
        # A more sophisticated version would check Huckel's 4n+2 rule explicitly
        score = 0.0
        for ring in aromatic_rings:
            n_atoms = len(ring)
            # Weight by pi-electron count approximation (assuming 1 pi-electron per aromatic atom)
            # 4n+2 rule: aromatic if pi_electrons = 4n+2
            # Here we just sum aromatic atoms as a proxy
            score += n_atoms
        
        # Normalize by total atoms
        total_atoms = mol.GetNumAtoms()
        if total_atoms == 0:
            return 0.0
        return float(score / total_atoms)
    except Exception as e:
        logger.warning(f"Error computing Hückel aromaticity index: {e}")
        return 0.0

def compute_aromatic_ring_count(mol: Chem.Mol) -> int:
    """Count the number of aromatic rings."""
    if mol is None:
        return 0
    
    try:
        aromatic_count = 0
        ring_info = mol.GetRingInfo()
        for ring in ring_info.AtomRings():
            if all(mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring):
                aromatic_count += 1
        return aromatic_count
    except Exception as e:
        logger.warning(f"Error computing aromatic ring count: {e}")
        return 0

def compute_bond_order_annotation(mol: Chem.Mol) -> float:
    """
    Estimate effective bond lengths based on bond types and hybridization.
    Returns an average 'effective bond length' deviation from single bond.
    """
    if mol is None:
        return 0.0
    
    try:
        total_deviation = 0.0
        count = 0
        
        for bond in mol.GetBonds():
            bond_type = bond.GetBondType()
            is_aromatic = bond.GetIsAromatic()
            
            if is_aromatic:
                ref_len = BOND_LENGTHS['AROMATIC']
            elif bond_type == Chem.BondType.DOUBLE:
                ref_len = BOND_LENGTHS['DOUBLE']
            elif bond_type == Chem.BondType.TRIPLE:
                ref_len = BOND_LENGTHS['TRIPLE']
            else:
                ref_len = BOND_LENGTHS['SINGLE']
            
            # Deviation from standard single bond
            deviation = BOND_LENGTHS['SINGLE'] - ref_len
            total_deviation += deviation
            count += 1
        
        if count == 0:
            return 0.0
        return float(total_deviation / count)
    except Exception as e:
        logger.warning(f"Error computing bond order annotation: {e}")
        return 0.0

def compute_bond_polarity(mol: Chem.Mol) -> float:
    """
    Calculate bond polarity using Pauling electronegativity differences.
    Formula: Sum of (|EN1 - EN2| * bond_length) for all bonds.
    """
    if mol is None:
        return 0.0
    
    try:
        total_polarity = 0.0
        count = 0
        
        for bond in mol.GetBonds():
            atom1 = bond.GetBeginAtom()
            atom2 = bond.GetEndAtom()
            
            en1 = ELECTRONEGATIVITY.get(atom1.GetAtomicNum(), 2.55)
            en2 = ELECTRONEGATIVITY.get(atom2.GetAtomicNum(), 2.55)
            
            diff = abs(en1 - en2)
            
            # Estimate bond length based on bond type
            if bond.GetIsAromatic():
                bond_len = BOND_LENGTHS['AROMATIC']
            elif bond.GetBondType() == Chem.BondType.DOUBLE:
                bond_len = BOND_LENGTHS['DOUBLE']
            elif bond.GetBondType() == Chem.BondType.TRIPLE:
                bond_len = BOND_LENGTHS['TRIPLE']
            else:
                bond_len = BOND_LENGTHS['SINGLE']
            
            total_polarity += diff * bond_len
            count += 1
        
        if count == 0:
            return 0.0
        return float(total_polarity / count)
    except Exception as e:
        logger.warning(f"Error computing bond polarity: {e}")
        return 0.0

def compute_resonance_energy(mol: Chem.Mol) -> float:
    """
    Estimate resonance energy using Hückel Molecular Orbital (HMO) approximations.
    Heuristic: Sum of aromatic ring contributions based on size.
    Benzene ~ 36 kcal/mol, Naphthalene ~ 61 kcal/mol, etc.
    Returns an approximate value in kcal/mol.
    """
    if mol is None:
        return 0.0
    
    try:
        total_energy = 0.0
        ring_info = mol.GetRingInfo()
        
        for ring in ring_info.AtomRings():
            # Check if aromatic
            if all(mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring):
                n = len(ring)
                # Hückel rule: 4n+2 pi electrons. 
                # Approximate energy contribution based on ring size.
                # Simplified model: Energy ~ k * (n - 2) for aromatic rings
                # Benzene (n=6) -> ~36 kcal/mol
                # Cyclopentadienyl (n=5) -> ~20 kcal/mol (approx)
                
                if n == 6:
                    energy = 36.0  # Benzene-like
                elif n == 5:
                    energy = 20.0  # Cyclopentadienyl-like
                elif n == 7:
                    energy = 30.0  # Tropylium-like
                elif n == 4:
                    energy = 0.0   # Cyclobutadiene is anti-aromatic
                else:
                    # Linear interpolation for others
                    energy = max(0.0, 10.0 * (n - 4))
                
                total_energy += energy
        
        return float(total_energy)
    except Exception as e:
        logger.warning(f"Error computing resonance energy: {e}")
        return 0.0

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """
    Compute all descriptors for a list of SMILES strings.
    Returns a DataFrame with the exact columns required by T019.
    """
    results = []
    
    for smiles in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                results.append({
                    'smiles': smiles,
                    'status': 'invalid',
                    'degree_mean': 0.0,
                    'degree_std': 0.0,
                    'degree_max': 0.0,
                    'degree_min': 0.0,
                    'path_length_mean': 0.0,
                    'path_length_std': 0.0,
                    'path_length_max': 0.0,
                    'path_length_min': 0.0,
                    'aromaticity_index': 0.0,
                    'conjugation_length': 0.0,
                    'ring_count': 0,
                    'bond_polarity': 0.0,
                    'resonance_energy': 0.0
                })
                continue
            
            # Compute standard descriptors
            deg_stats = compute_degree_statistics(mol)
            path_stats = compute_path_length_statistics(mol)
            ring_cnt = compute_ring_count(mol)
            arom_idx = compute_huckel_aromaticity_index(mol)
            arom_ring_cnt = compute_aromatic_ring_count(mol)
            bond_order = compute_bond_order_annotation(mol)
            bond_pol = compute_bond_polarity(mol)
            res_energy = compute_resonance_energy(mol)
            
            # Conjugation length: number of conjugated atoms (heuristic)
            # Approximate as number of aromatic atoms + sp2 atoms in double bonds
            conjugated_count = 0
            for atom in mol.GetAtoms():
                if atom.GetIsAromatic() or atom.GetHybridization() == Chem.HybridizationType.SP2:
                    conjugated_count += 1
            
            results.append({
                'smiles': smiles,
                'status': 'valid',
                'degree_mean': deg_stats['mean'],
                'degree_std': deg_stats['std'],
                'degree_max': deg_stats['max'],
                'degree_min': deg_stats['min'],
                'path_length_mean': path_stats['mean'],
                'path_length_std': path_stats['std'],
                'path_length_max': path_stats['max'],
                'path_length_min': path_stats['min'],
                'aromaticity_index': arom_idx,
                'conjugation_length': float(conjugated_count),
                'ring_count': ring_cnt,
                'bond_polarity': bond_pol,
                'resonance_energy': res_energy
            })
            
        except Exception as e:
            logger.error(f"Error processing {smiles}: {e}")
            results.append({
                'smiles': smiles,
                'status': 'error',
                'degree_mean': 0.0,
                'degree_std': 0.0,
                'degree_max': 0.0,
                'degree_min': 0.0,
                'path_length_mean': 0.0,
                'path_length_std': 0.0,
                'path_length_max': 0.0,
                'path_length_min': 0.0,
                'aromaticity_index': 0.0,
                'conjugation_length': 0.0,
                'ring_count': 0,
                'bond_polarity': 0.0,
                'resonance_energy': 0.0
            })
    
    df = pd.DataFrame(results)
    
    # Ensure no NaN values
    df = df.fillna(0.0)
    
    # Ensure correct column order
    expected_cols = [
        'smiles', 'status', 'degree_mean', 'degree_std', 'degree_max', 'degree_min',
        'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
        'aromaticity_index', 'conjugation_length', 'ring_count', 'bond_polarity', 'resonance_energy'
    ]
    
    df = df[expected_cols]
    
    return df

def compute_standard_descriptors(mol: Chem.Mol) -> Dict[str, Any]:
    """Wrapper for standard descriptors."""
    if mol is None:
        return {}
    
    return {
        'degree_stats': compute_degree_statistics(mol),
        'path_stats': compute_path_length_statistics(mol),
        'ring_count': compute_ring_count(mol),
        'aromaticity_index': compute_huckel_aromaticity_index(mol),
        'aromatic_ring_count': compute_aromatic_ring_count(mol)
    }
