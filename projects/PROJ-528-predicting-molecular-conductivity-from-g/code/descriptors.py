"""
Compute graph-based molecular descriptors using RDKit.
Implements standard topological descriptors, aromaticity metrics, conjugation analysis,
and resonance proxies as specified in FR-001 and FR-008.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdmolops
from rdkit.Chem.Scaffolds import MurckoScaffold

def compute_degree_statistics(mol: Chem.Mol) -> Dict[str, float]:
    """
    Compute degree-based graph descriptors.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Dictionary with degree_mean, degree_std, degree_max, degree_min
    """
    try:
        degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
        if not degrees:
            return {'degree_mean': np.nan, 'degree_std': np.nan, 
                    'degree_max': np.nan, 'degree_min': np.nan}
        
        return {
            'degree_mean': np.mean(degrees),
            'degree_std': np.std(degrees),
            'degree_max': max(degrees),
            'degree_min': min(degrees)
        }
    except Exception as e:
        logging.warning(f"Error computing degree statistics: {e}")
        return {'degree_mean': np.nan, 'degree_std': np.nan, 
                'degree_max': np.nan, 'degree_min': np.nan}

def compute_path_length_statistics(mol: Chem.Mol) -> Dict[str, float]:
    """
    Compute path length-based graph descriptors.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Dictionary with path_length_mean, path_length_std, path_length_max, path_length_min
    """
    try:
        # Get all pairs of atoms and their shortest path lengths
        distances = []
        for i in range(mol.GetNumAtoms()):
            for j in range(i + 1, mol.GetNumAtoms()):
                dist = rdmolops.GetShortestPath(mol, i, j)
                if dist is not None:
                    distances.append(len(dist) - 1)  # Convert to edge count
        
        if not distances:
            return {'path_length_mean': np.nan, 'path_length_std': np.nan,
                    'path_length_max': np.nan, 'path_length_min': np.nan}
        
        return {
            'path_length_mean': np.mean(distances),
            'path_length_std': np.std(distances),
            'path_length_max': max(distances),
            'path_length_min': min(distances)
        }
    except Exception as e:
        logging.warning(f"Error computing path length statistics: {e}")
        return {'path_length_mean': np.nan, 'path_length_std': np.nan,
                'path_length_max': np.nan, 'path_length_min': np.nan}

def compute_ring_count(mol: Chem.Mol) -> int:
    """
    Compute the number of rings in the molecule.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Number of rings
    """
    try:
        return mol.GetRingInfo().NumRings()
    except Exception as e:
        logging.warning(f"Error computing ring count: {e}")
        return np.nan

def compute_aromaticity_index(mol: Chem.Mol) -> float:
    """
    Compute the aromaticity index (ratio of aromatic atoms to total atoms).
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Aromaticity index between 0 and 1
    """
    try:
        if mol.GetNumAtoms() == 0:
            return np.nan
        
        aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
        return aromatic_atoms / mol.GetNumAtoms()
    except Exception as e:
        logging.warning(f"Error computing aromaticity index: {e}")
        return np.nan

def compute_huckel_aromaticity_count(mol: Chem.Mol) -> int:
    """
    Count rings that satisfy Hückel's rule (4n+2 π electrons).
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Number of Hückel-aromatic rings
    """
    try:
      count = 0
      ring_info = mol.GetRingInfo()
      for ring in ring_info.AtomRings():
          # Check if ring is aromatic
          if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
              # Count π electrons (simplified: assume sp2 atoms contribute 1 π electron)
              pi_electrons = sum(1 for i in ring if mol.GetAtomWithIdx(i).GetIsAromatic())
              # Check Hückel's rule: 4n+2
              n = (pi_electrons - 2) / 4
              if n >= 0 and abs(n - round(n)) < 1e-6:
                  count += 1
      return count
    except Exception as e:
        logging.warning(f"Error computing Hückel aromaticity count: {e}")
        return np.nan

def compute_clar_aromaticity_proxy(mol: Chem.Mol) -> int:
    """
    Compute a proxy for Clar aromaticity (number of disjoint aromatic sextets).
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Clar aromaticity proxy count
    """
    try:
        # Simplified proxy: count benzene-like rings (6-membered aromatic rings)
        count = 0
        ring_info = mol.GetRingInfo()
        for ring in ring_info.AtomRings():
            if len(ring) == 6:
                if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
                    count += 1
        return count
    except Exception as e:
        logging.warning(f"Error computing Clar aromaticity proxy: {e}")
        return np.nan

def compute_conjugation_length(mol: Chem.Mol) -> float:
    """
    Compute the longest conjugated path length in the molecule.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Longest conjugated path length
    """
    try:
        # Find conjugated bonds (alternating single/double or aromatic)
        conjugated_bonds = []
        for bond in mol.GetBonds():
            if bond.GetBondType() == Chem.BondType.DOUBLE or \
               bond.GetBondType() == Chem.BondType.AROMATIC or \
               bond.GetBondType() == Chem.BondType.SINGLE:
                # Check if this bond is part of a conjugated system
                begin_atom = bond.GetBeginAtom()
                end_atom = bond.GetEndAtom()
                if begin_atom.GetIsAromatic() or end_atom.GetIsAromatic() or \
                   begin_atom.GetHybridization() == Chem.HybridizationType.SP2 or \
                   end_atom.GetHybridization() == Chem.HybridizationType.SP2:
                    conjugated_bonds.append(bond.GetIdx())
        
        if not conjugated_bonds:
            return 0.0
        
        # Build graph of conjugated bonds and find longest path
        # Simplified: count number of conjugated bonds
        return len(conjugated_bonds)
    except Exception as e:
        logging.warning(f"Error computing conjugation length: {e}")
        return np.nan

def compute_num_conjugated_bonds(mol: Chem.Mol) -> int:
    """
    Count the number of conjugated bonds in the molecule.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Number of conjugated bonds
    """
    try:
        count = 0
        for bond in mol.GetBonds():
            if bond.GetBondType() == Chem.BondType.DOUBLE or \
               bond.GetBondType() == Chem.BondType.AROMATIC:
                count += 1
            elif bond.GetBondType() == Chem.BondType.SINGLE:
                # Check if adjacent to double/aromatic bonds
                begin_atom = bond.GetBeginAtom()
                end_atom = bond.GetEndAtom()
                begin_neighbors = [a.GetIsAromatic() or a.GetHybridization() == Chem.HybridizationType.SP2 
                                 for a in begin_atom.GetNeighbors()]
                end_neighbors = [a.GetIsAromatic() or a.GetHybridization() == Chem.HybridizationType.SP2 
                               for a in end_atom.GetNeighbors()]
                if any(begin_neighbors) or any(end_neighbors):
                    count += 1
        return count
    except Exception as e:
        logging.warning(f"Error computing number of conjugated bonds: {e}")
        return np.nan

def compute_conjugation_density(mol: Chem.Mol) -> float:
    """
    Compute conjugation density (conjugated bonds / total bonds).
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Conjugation density between 0 and 1
    """
    try:
        if mol.GetNumBonds() == 0:
            return np.nan
        
        num_conjugated = compute_num_conjugated_bonds(mol)
        return num_conjugated / mol.GetNumBonds()
    except Exception as e:
        logging.warning(f"Error computing conjugation density: {e}")
        return np.nan

def compute_aromatic_ring_count(mol: Chem.Mol) -> int:
    """
    Count the number of aromatic rings using RDKit's built-in methods.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Number of aromatic rings
    """
    try:
        return rdMolDescriptors.CalcNumAromaticRings(mol)
    except Exception as e:
        logging.warning(f"Error computing aromatic ring count: {e}")
        return np.nan

def compute_conjugated_ring_count(mol: Chem.Mol) -> int:
    """
    Count the number of conjugated rings (rings with alternating double bonds).
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Number of conjugated rings
    """
    try:
        # Simplified: count rings that are aromatic or have conjugated bonds
        count = 0
        ring_info = mol.GetRingInfo()
        for ring in ring_info.AtomRings():
            # Check if ring has any conjugated bonds
            has_conjugated = False
            for i in range(len(ring)):
                atom1 = mol.GetAtomWithIdx(ring[i])
                atom2 = mol.GetAtomWithIdx(ring[(i + 1) % len(ring)])
                bond = mol.GetBondBetweenAtoms(ring[i], ring[(i + 1) % len(ring)])
                if bond and (bond.GetBondType() == Chem.BondType.DOUBLE or 
                           bond.GetBondType() == Chem.BondType.AROMATIC):
                    has_conjugated = True
                    break
            if has_conjugated:
                count += 1
        return count
    except Exception as e:
        logging.warning(f"Error computing conjugated ring count: {e}")
        return np.nan

def compute_standard_descriptors(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Compute a set of standard RDKit descriptors.
    
    Args:
        mol: RDKit Mol object
        
    Returns:
        Dictionary of standard descriptors
    """
    try:
        return {
            'mol_wt': Descriptors.MolWt(mol),
            'logp': Descriptors.MolLogP(mol),
            'num_h_donors': Descriptors.NumHDonors(mol),
            'num_h_acceptors': Descriptors.NumHAcceptors(mol),
            'num_rotatable_bonds': Descriptors.NumRotatableBonds(mol),
            'tpsa': Descriptors.TPSA(mol),
        }
    except Exception as e:
        logging.warning(f"Error computing standard descriptors: {e}")
        return {}

def compute_all_descriptors(smiles_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all descriptors for a dataframe of SMILES strings.
    
    Args:
        smiles_df: DataFrame with 'smiles' column
        
    Returns:
        DataFrame with all computed descriptors
    """
    results = []
    
    for idx, row in smiles_df.iterrows():
        smiles = row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        
        if mol is None:
            logging.warning(f"Invalid SMILES at index {idx}: {smiles}")
            results.append({
                'smiles': smiles,
                'status': 'invalid',
                'error_msg': 'Invalid SMILES'
            })
            continue
        
        try:
            descriptor_row = {
                'smiles': smiles,
                'status': 'valid',
                **compute_degree_statistics(mol),
                **compute_path_length_statistics(mol),
                'ring_count': compute_ring_count(mol),
                'aromaticity_index': compute_aromaticity_index(mol),
                'huckel_aromaticity_count': compute_huckel_aromaticity_count(mol),
                'clar_aromaticity_proxy': compute_clar_aromaticity_proxy(mol),
                'conjugation_length': compute_conjugation_length(mol),
                'num_conjugated_bonds': compute_num_conjugated_bonds(mol),
                'conjugation_density': compute_conjugation_density(mol),
                'aromatic_ring_count': compute_aromatic_ring_count(mol),
                'conjugated_ring_count': compute_conjugated_ring_count(mol),
            }
            
            # Add standard descriptors
            std_desc = compute_standard_descriptors(mol)
            descriptor_row.update(std_desc)
            
            results.append(descriptor_row)
            
        except Exception as e:
            logging.warning(f"Error computing descriptors for {smiles}: {e}")
            results.append({
                'smiles': smiles,
                'status': 'error',
                'error_msg': str(e)
            })
    
    return pd.DataFrame(results)

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """
    Compute descriptors for a list of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings
        
    Returns:
        DataFrame with computed descriptors
    """
    smiles_df = pd.DataFrame({'smiles': smiles_list})
    return compute_all_descriptors(smiles_df)
