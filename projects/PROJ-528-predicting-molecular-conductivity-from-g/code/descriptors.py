"""
Molecular Descriptor Computation Module (T014a-d)

Computes graph-based descriptors using RDKit:
- T014a: Base Graph Descriptors
- T014b: Aromaticity & Ring Descriptors
- T014c: Conjugation Descriptors
- T014d: Resonance Proxies (RDKit Only)
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdmolops
from rdkit.Chem.Scaffolds import MurckoScaffold
from code.logging_config import setup_logging

# Set up logger
logger = setup_logging()

def compute_degree_statistics(mol: Chem.Mol) -> Dict[str, float]:
    """T014a: Compute degree statistics (mean, std, max, min)."""
    try:
        degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
        if not degrees:
            return {'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan}
        
        return {
            'degree_mean': float(np.mean(degrees)),
            'degree_std': float(np.std(degrees)),
            'degree_max': float(np.max(degrees)),
            'degree_min': float(np.min(degrees))
        }
    except Exception as e:
        logger.warning(f"Degree statistics computation failed: {e}")
        return {'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan}

def compute_path_length_statistics(mol: Chem.Mol) -> Dict[str, float]:
    """T014a: Compute path length statistics (mean, std, max, min)."""
    try:
        # Get all pairs shortest paths
        dist_matrix = rdmolops.GetDistanceMatrix(mol)
        
        # Extract upper triangle (excluding diagonal)
        paths = []
        n = dist_matrix.shape[0]
        for i in range(n):
            for j in range(i + 1, n):
                if dist_matrix[i, j] > 0:  # Exclude self-loops
                    paths.append(dist_matrix[i, j])
        
        if not paths:
            return {'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan}
        
        return {
            'path_length_mean': float(np.mean(paths)),
            'path_length_std': float(np.std(paths)),
            'path_length_max': float(np.max(paths)),
            'path_length_min': float(np.min(paths))
        }
    except Exception as e:
        logger.warning(f"Path length statistics computation failed: {e}")
        return {'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan}

def compute_aromaticity_index(mol: Chem.Mol) -> float:
    """T014b: Compute aromaticity index (fraction of aromatic atoms)."""
    try:
        total_atoms = mol.GetNumAtoms()
        if total_atoms == 0:
            return np.nan
        
        aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
        return float(aromatic_atoms / total_atoms)
    except Exception as e:
        logger.warning(f"Aromaticity index computation failed: {e}")
        return np.nan

def compute_ring_count(mol: Chem.Mol) -> int:
    """T014b: Compute total ring count."""
    try:
        return int(Chem.GetSSSR(mol))
    except Exception as e:
        logger.warning(f"Ring count computation failed: {e}")
        return np.nan

def compute_conjugation_length(mol: Chem.Mol) -> float:
    """T014c: Compute longest conjugated path length."""
    try:
        # Identify conjugated bonds (alternating single/double or aromatic)
        conjugated_bonds = []
        for bond in mol.GetBonds():
            bond_type = bond.GetBondType()
            if bond_type in [Chem.BondType.DOUBLE, Chem.BondType.TRIPLE, Chem.BondType.AROMATIC]:
                conjugated_bonds.append(bond.GetIdx())
        
        if not conjugated_bonds:
            return 0.0
        
        # Build conjugated subgraph and find longest path
        # Simplified: count consecutive conjugated bonds
        max_path = 0
        current_path = 0
        
        for i, bond in enumerate(mol.GetBonds()):
            if bond.GetIdx() in conjugated_bonds:
                current_path += 1
                max_path = max(max_path, current_path)
            else:
                current_path = 0
        
        return float(max_path)
    except Exception as e:
        logger.warning(f"Conjugation length computation failed: {e}")
        return np.nan

def compute_num_conjugated_bonds(mol: Chem.Mol) -> int:
    """T014c: Count number of conjugated bonds."""
    try:
        count = 0
        for bond in mol.GetBonds():
            bond_type = bond.GetBondType()
            if bond_type in [Chem.BondType.DOUBLE, Chem.BondType.TRIPLE, Chem.BondType.AROMATIC]:
                count += 1
        return count
    except Exception as e:
        logger.warning(f"Conjugated bond count computation failed: {e}")
        return np.nan

def compute_conjugation_density(mol: Chem.Mol) -> float:
    """T014c: Compute conjugation density (conjugated bonds / total bonds)."""
    try:
        total_bonds = mol.GetNumBonds()
        if total_bonds == 0:
            return np.nan
        
        conjugated_count = compute_num_conjugated_bonds(mol)
        return float(conjugated_count / total_bonds)
    except Exception as e:
        logger.warning(f"Conjugation density computation failed: {e}")
        return np.nan

def compute_aromatic_ring_count(mol: Chem.Mol) -> int:
    """T014d: Count aromatic rings using RDKit."""
    try:
        return rdMolDescriptors.CalcNumAromaticRings(mol)
    except Exception as e:
        logger.warning(f"Aromatic ring count computation failed: {e}")
        return np.nan

def compute_conjugated_ring_count(mol: Chem.Mol) -> int:
    """T014d: Count conjugated rings (rings with alternating double bonds)."""
    try:
        # Approximation: count rings with at least one aromatic bond
        rings = list(Chem.GetSymmSSSR(mol))
        count = 0
        for ring in rings:
            has_conjugated = False
            for idx in ring:
                bond = mol.GetBondWithIdx(idx)
                if bond.GetBondType() in [Chem.BondType.DOUBLE, Chem.BondType.AROMATIC]:
                    has_conjugated = True
                    break
            if has_conjugated:
                count += 1
        return count
    except Exception as e:
        logger.warning(f"Conjugated ring count computation failed: {e}")
        return np.nan

def compute_all_descriptors(smiles_list: List[str]) -> List[Dict[str, Any]]:
    """
    Compute all descriptors for a list of SMILES strings.
    Returns list of dictionaries with descriptor values.
    """
    results = []
    
    for i, smiles in enumerate(smiles_list):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.warning(f"Invalid SMILES at index {i}: {smiles}")
                results.append({
                    'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan,
                    'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan,
                    'aromaticity_index': np.nan, 'ring_count': np.nan,
                    'conjugation_length': np.nan, 'num_conjugated_bonds': np.nan, 'conjugation_density': np.nan,
                    'aromatic_ring_count': np.nan, 'conjugated_ring_count': np.nan
                })
                continue
            
            # T014a: Base Graph Descriptors
            degree_stats = compute_degree_statistics(mol)
            path_stats = compute_path_length_statistics(mol)
            
            # T014b: Aromaticity & Ring Descriptors
            aromaticity_idx = compute_aromaticity_index(mol)
            ring_cnt = compute_ring_count(mol)
            
            # T014c: Conjugation Descriptors
            conj_len = compute_conjugation_length(mol)
            num_conj_bonds = compute_num_conjugated_bonds(mol)
            conj_density = compute_conjugation_density(mol)
            
            # T014d: Resonance Proxies
            arom_ring_cnt = compute_aromatic_ring_count(mol)
            conj_ring_cnt = compute_conjugated_ring_count(mol)
            
            result = {
                **degree_stats,
                **path_stats,
                'aromaticity_index': aromaticity_idx,
                'ring_count': ring_cnt,
                'conjugation_length': conj_len,
                'num_conjugated_bonds': num_conj_bonds,
                'conjugation_density': conj_density,
                'aromatic_ring_count': arom_ring_cnt,
                'conjugated_ring_count': conj_ring_cnt
            }
            
            results.append(result)
            
        except Exception as e:
            logger.warning(f"Descriptor computation failed for SMILES {i}: {e}")
            results.append({
                'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan,
                'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan,
                'aromaticity_index': np.nan, 'ring_count': np.nan,
                'conjugation_length': np.nan, 'num_conjugated_bonds': np.nan, 'conjugation_density': np.nan,
                'aromatic_ring_count': np.nan, 'conjugated_ring_count': np.nan
            })
    
    return results

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """
    Compute descriptors for a batch of SMILES and return as DataFrame.
    """
    results = compute_all_descriptors(smiles_list)
    return pd.DataFrame(results)
