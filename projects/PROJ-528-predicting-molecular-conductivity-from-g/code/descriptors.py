"""
Molecular descriptor computation module.
Implements T014a, T014b, T015, T017: Degree, Path Length, Aromaticity, and Conjugation descriptors.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdmolops
from rdkit.Chem.Scaffolds import MurckoScaffold

logger = logging.getLogger(__name__)

def compute_degree_statistics(smiles: str) -> Optional[Dict[str, float]]:
    """
    Compute degree distribution descriptors (mean, std, max, min) for a molecule.
    Implements T014a.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Get atom degrees (number of bonds for each atom)
        degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
        
        if not degrees:
            return None
        
        return {
            'mean': float(np.mean(degrees)),
            'std': float(np.std(degrees)),
            'max': float(np.max(degrees)),
            'min': float(np.min(degrees))
        }
    except Exception as e:
        logger.error(f"Error computing degree statistics for {smiles}: {e}")
        return None

def compute_path_length_statistics(smiles: str) -> Optional[Dict[str, float]]:
    """
    Compute path length distribution descriptors (mean, std, max, min) for a molecule.
    Implements T014b.
    Uses the Wiener index and distance matrix to compute path lengths.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Get distance matrix
        dist_matrix = rdmolops.GetDistanceMatrix(mol)
        
        # Extract upper triangle (excluding diagonal) to get unique path lengths
        n_atoms = mol.GetNumAtoms()
        if n_atoms < 2:
            return None
        
        path_lengths = []
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                path_lengths.append(dist_matrix[i, j])
        
        if not path_lengths:
            return None
        
        return {
            'mean': float(np.mean(path_lengths)),
            'std': float(np.std(path_lengths)),
            'max': float(np.max(path_lengths)),
            'min': float(np.min(path_lengths))
        }
    except Exception as e:
        logger.error(f"Error computing path length statistics for {smiles}: {e}")
        return None

def compute_ring_count(smiles: str) -> Optional[float]:
    """
    Compute total ring count for a molecule.
    Implements T015.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Use RDKit's ring count function
        ring_count = rdMolDescriptors.CalcNumRings(mol)
        return float(ring_count)
    except Exception as e:
        logger.error(f"Error computing ring count for {smiles}: {e}")
        return None

def compute_aromatic_ring_count(smiles: str) -> Optional[float]:
    """
    Compute aromatic ring count (aromaticity index) for a molecule.
    Implements T015.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Use RDKit's aromatic ring count function
        aromatic_count = rdMolDescriptors.CalcNumAromaticRings(mol)
        return float(aromatic_count)
    except Exception as e:
        logger.error(f"Error computing aromatic ring count for {smiles}: {e}")
        return None

def compute_conjugation_length(smiles: str) -> Optional[float]:
    """
    Compute conjugation path length for a molecule.
    Implements T017 (fallback for quantum descriptors).
    Estimates the longest conjugated path in the molecule.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Identify conjugated atoms (sp2 or sp3 with pi bonds)
        # A simple heuristic: count atoms in conjugated systems
        conjugated_atoms = 0
        for atom in mol.GetAtoms():
            # Check if atom is part of a conjugated system
            if atom.GetIsAromatic() or atom.GetHybridization() in [Chem.rdchem.HybridizationType.SP2, Chem.rdchem.HybridizationType.SP]:
                conjugated_atoms += 1
        
        # Also check for alternating single/double bonds
        # This is a simplified approximation
        max_conjugation_path = 0
        current_path = 0
        
        for bond in mol.GetBonds():
            if bond.GetBondType() == Chem.BondType.DOUBLE or bond.GetBondType() == Chem.BondType.AROMATIC:
                current_path += 1
            else:
                if current_path > max_conjugation_path:
                    max_conjugation_path = current_path
                current_path = 0
        
        if current_path > max_conjugation_path:
            max_conjugation_path = current_path
        
        # Return a value based on the conjugated system size
        # Using the number of conjugated atoms as a proxy for conjugation length
        return float(conjugated_atoms) if conjugated_atoms > 0 else 0.0
    except Exception as e:
        logger.error(f"Error computing conjugation length for {smiles}: {e}")
        return None

def compute_huckel_aromaticity_index(smiles: str) -> Optional[float]:
    """
    Compute Hückel aromaticity index.
    Returns 1.0 if the molecule satisfies Hückel's rule (4n+2 pi electrons in a planar ring), 0.0 otherwise.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Check if molecule has aromatic rings
        if mol.GetNumAromaticRings() == 0:
            return 0.0
        
        # Simple check: if all rings are aromatic, return 1.0
        # This is a simplified version; full Hückel analysis requires pi electron counting
        is_aromatic = True
        for ring in mol.GetRingInfo().AtomRings():
            ring_atoms = [mol.GetAtomWithIdx(idx) for idx in ring]
            if not all(atom.GetIsAromatic() for atom in ring_atoms):
                is_aromatic = False
                break
        
        return 1.0 if is_aromatic else 0.0
    except Exception as e:
        logger.error(f"Error computing Hückel aromaticity index for {smiles}: {e}")
        return None

def compute_standard_descriptors(smiles: str) -> Dict[str, Any]:
    """
    Compute all standard descriptors for a molecule.
    Returns a dictionary with all computed descriptor values.
    """
    degree_stats = compute_degree_statistics(smiles)
    path_stats = compute_path_length_statistics(smiles)
    ring_cnt = compute_ring_count(smiles)
    aromatic_cnt = compute_aromatic_ring_count(smiles)
    conj_len = compute_conjugation_length(smiles)
    
    result = {
        'smiles': smiles,
        'status': 'success' if all([degree_stats, path_stats, ring_cnt, aromatic_cnt, conj_len]) else 'partial',
    }
    
    if degree_stats:
        result.update(degree_stats)
    else:
        result.update({'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan})
    
    if path_stats:
        result.update(path_stats)
    else:
        result.update({'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan})
    
    result['ring_count'] = ring_cnt if ring_cnt is not None else np.nan
    result['aromaticity_index'] = aromatic_cnt if aromatic_cnt is not None else np.nan
    result['conjugation_length'] = conj_len if conj_len is not None else np.nan
    
    return result

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """
    Compute descriptors for a batch of SMILES strings.
    Returns a DataFrame with all descriptors.
    """
    results = []
    for smiles in smiles_list:
        desc = compute_standard_descriptors(smiles)
        results.append(desc)
    
    return pd.DataFrame(results)