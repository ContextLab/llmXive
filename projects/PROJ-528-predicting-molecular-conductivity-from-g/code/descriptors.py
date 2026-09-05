import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdmolops
from rdkit.Chem.Scaffolds import MurckoScaffold

def compute_degree_statistics(mol: Chem.rdchem.Mol) -> Dict[str, float]:
    """Compute mean, std, max, min of atom degrees."""
    if mol is None:
        return {'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan}
    
    degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
    if not degrees:
        return {'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan}
    
    return {
        'degree_mean': float(np.mean(degrees)),
        'degree_std': float(np.std(degrees)),
        'degree_max': float(np.max(degrees)),
        'degree_min': float(np.min(degrees))
    }

def compute_path_length_statistics(mol: Chem.rdchem.Mol) -> Dict[str, float]:
    """Compute mean, std, max, min of shortest path lengths."""
    if mol is None:
        return {'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan}
    
    try:
        dist_matrix = rdmolops.GetDistanceMatrix(mol)
        # Get upper triangle values (excluding diagonal)
        paths = []
        n = dist_matrix.shape[0]
        for i in range(n):
            for j in range(i+1, n):
                if dist_matrix[i, j] > 0:
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
        logging.warning(f"Path length calculation failed: {e}")
        return {'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan}

def compute_ring_count(mol: Chem.rdchem.Mol) -> Dict[str, int]:
    """Compute number of rings."""
    if mol is None:
        return {'ring_count': 0}
    try:
        return {'ring_count': mol.GetRingInfo().NumRings()}
    except Exception:
        return {'ring_count': 0}

def compute_aromatic_ring_count(mol: Chem.rdchem.Mol) -> Dict[str, int]:
    """Compute number of aromatic rings."""
    if mol is None:
        return {'aromaticity_index': 0}
    try:
        return {'aromaticity_index': rdMolDescriptors.CalcNumAromaticRings(mol)}
    except Exception:
        return {'aromaticity_index': 0}

def compute_huckel_aromaticity_count(mol: Chem.rdchem.Mol) -> Dict[str, int]:
    """Count aromatic rings (Huckel proxy)."""
    if mol is None:
        return {'huckel_aromaticity_count': 0}
    try:
        return {'huckel_aromaticity_count': rdMolDescriptors.CalcNumAromaticRings(mol)}
    except Exception:
        return {'huckel_aromaticity_count': 0}

def compute_clar_aromaticity_proxy(mol: Chem.rdchem.Mol) -> Dict[str, int]:
    """Approximate Clar aromatic sextets by counting maximum independent set of aromatic rings (heuristic)."""
    if mol is None:
        return {'clar_aromaticity_proxy': 0}
    # Simplified: just return aromatic ring count as a proxy for now
    # A true Clar sextet calculation is complex and requires graph theory on the ring system
    try:
        num_aromatic = rdMolDescriptors.CalcNumAromaticRings(mol)
        return {'clar_aromaticity_proxy': num_aromatic} 
    except Exception:
        return {'clar_aromaticity_proxy': 0}

def compute_conjugation_length(mol: Chem.rdchem.Mol) -> Dict[str, float]:
    """Compute longest conjugated path length (heuristic)."""
    if mol is None:
        return {'conjugation_length': np.nan}
    
    try:
        # Identify conjugated bonds (order > 1 or aromatic)
        conjugated_bonds = []
        for bond in mol.GetBonds():
            if bond.GetBondTypeAsDouble() > 1.0 or bond.GetIsAromatic():
                conjugated_bonds.append(bond.GetIdx())
        
        if not conjugated_bonds:
            return {'conjugation_length': np.nan}
        
        # Build adjacency for conjugated bonds only
        adj = {i: [] for i in range(mol.GetNumAtoms())}
        for bond in mol.GetBonds():
            if bond.GetIdx() in conjugated_bonds:
                i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
                adj[i].append(j)
                adj[j].append(i)
        
        # DFS to find longest path
        max_len = 0
        visited_global = set()
        
        def dfs(node, visited, length):
            nonlocal max_len
            max_len = max(max_len, length)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    dfs(neighbor, visited, length + 1)
                    visited.remove(neighbor)
        
        # Try starting from each node in the conjugated system
        start_nodes = set()
        for idx in conjugated_bonds:
            bond = mol.GetBondWithIdx(idx)
            start_nodes.add(bond.GetBeginAtomIdx())
            start_nodes.add(bond.GetEndAtomIdx())
        
        for start in start_nodes:
            dfs(start, {start}, 0)
        
        return {'conjugation_length': float(max_len)}
    except Exception as e:
        logging.warning(f"Conjugation length calculation failed: {e}")
        return {'conjugation_length': np.nan}

def compute_num_conjugated_bonds(mol: Chem.rdchem.Mol) -> Dict[str, int]:
    """Count conjugated bonds."""
    if mol is None:
        return {'num_conjugated_bonds': 0}
    count = 0
    for bond in mol.GetBonds():
        if bond.GetBondTypeAsDouble() > 1.0 or bond.GetIsAromatic():
            count += 1
    return {'num_conjugated_bonds': count}

def compute_conjugation_density(mol: Chem.rdchem.Mol) -> Dict[str, float]:
    """Ratio of conjugated bonds to total bonds."""
    if mol is None:
        return {'conjugation_density': np.nan}
    total = mol.GetNumBonds()
    if total == 0:
        return {'conjugation_density': np.nan}
    conj = compute_num_conjugated_bonds(mol)['num_conjugated_bonds']
    return {'conjugation_density': float(conj / total)}

def compute_standard_descriptors(smiles: str) -> Dict[str, Any]:
    """Compute all standard descriptors for a SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {
            'degree_mean': np.nan, 'degree_std': np.nan, 'degree_max': np.nan, 'degree_min': np.nan,
            'path_length_mean': np.nan, 'path_length_std': np.nan, 'path_length_max': np.nan, 'path_length_min': np.nan,
            'aromaticity_index': np.nan, 'huckel_aromaticity_count': np.nan, 'clar_aromaticity_proxy': np.nan,
            'conjugation_length': np.nan, 'num_conjugated_bonds': np.nan, 'conjugation_density': np.nan,
            'ring_count': 0
        }
    
    desc = {}
    desc.update(compute_degree_statistics(mol))
    desc.update(compute_path_length_statistics(mol))
    desc.update(compute_ring_count(mol))
    desc.update(compute_aromatic_ring_count(mol))
    desc.update(compute_huckel_aromaticity_count(mol))
    desc.update(compute_clar_aromaticity_proxy(mol))
    desc.update(compute_conjugation_length(mol))
    desc.update(compute_num_conjugated_bonds(mol))
    desc.update(compute_conjugation_density(mol))
    
    return desc

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """Compute descriptors for a list of SMILES."""
    results = []
    for s in smiles_list:
        desc = compute_standard_descriptors(s)
        desc['smiles'] = s
        results.append(desc)
    return pd.DataFrame(results)