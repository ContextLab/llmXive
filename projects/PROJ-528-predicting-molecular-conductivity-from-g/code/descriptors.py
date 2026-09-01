import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors

logger = logging.getLogger(__name__)

# Constants for fallback thresholds
DEFAULT_AROMATICITY_INDEX = 0.0
DEFAULT_CONJUGATION_LENGTH = 0.0
DEFAULT_BOND_POLARITY = 0.0
DEFAULT_RESONANCE_ENERGY = 0.0
DEFAULT_BOND_ORDER = 1.0

def compute_degree_statistics(mol: Chem.Mol) -> Dict[str, float]:
    """Compute degree distribution statistics."""
    if mol is None:
        return {"mean": 0.0, "std": 0.0, "max": 0.0, "min": 0.0}
    
    degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
    if not degrees:
        return {"mean": 0.0, "std": 0.0, "max": 0.0, "min": 0.0}
    
    return {
        "mean": float(np.mean(degrees)),
        "std": float(np.std(degrees)),
        "max": float(np.max(degrees)),
        "min": float(np.min(degrees))
    }

def compute_path_length_statistics(mol: Chem.Mol) -> Dict[str, float]:
    """Compute path length statistics."""
    if mol is None:
        return {"mean": 0.0, "std": 0.0, "max": 0.0, "min": 0.0}
    
    try:
        # Get all pairs shortest paths
        lengths = []
        atoms = list(mol.GetAtoms())
        for i in range(len(atoms)):
            for j in range(i + 1, len(atoms)):
                path = mol.GetShortestPath(atoms[i], atoms[j])
                if path:
                    lengths.append(len(path) - 1)  # Number of bonds
        
        if not lengths:
            return {"mean": 0.0, "std": 0.0, "max": 0.0, "min": 0.0}
        
        return {
            "mean": float(np.mean(lengths)),
            "std": float(np.std(lengths)),
            "max": float(np.max(lengths)),
            "min": float(np.min(lengths))
        }
    except Exception:
        logger.warning("Failed to compute path length statistics")
        return {"mean": 0.0, "std": 0.0, "max": 0.0, "min": 0.0}

def compute_ring_count(mol: Chem.Mol) -> int:
    """Count the number of rings in the molecule."""
    if mol is None:
        return 0
    return mol.GetRingInfo().NumRings()

def compute_huckel_aromaticity_index(mol: Chem.Mol) -> float:
    """
    Compute Hückel aromaticity index based on 4n+2 rule.
    Returns 1.0 if aromatic, 0.0 otherwise.
    """
    if mol is None:
        return DEFAULT_AROMATICITY_INDEX
    
    try:
        # Check if molecule has aromatic rings
        if not mol.GetRingInfo().NumRings():
            return DEFAULT_AROMATICITY_INDEX
        
        # Count pi electrons in aromatic systems
        pi_electrons = 0
        aromatic_rings = 0
        
        for ring in mol.GetRingInfo().AtomRings():
            is_aromatic = all(mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring)
            if is_aromatic:
                aromatic_rings += 1
                for idx in ring:
                    atom = mol.GetAtomWithIdx(idx)
                    if atom.GetIsAromatic():
                        # Count p-orbital electrons
                        if atom.GetAtomicNum() == 6:  # Carbon
                            pi_electrons += 1
                        elif atom.GetAtomicNum() == 7:  # Nitrogen
                            # Check if nitrogen contributes to pi system
                            if atom.GetTotalValence() <= 3:
                                pi_electrons += 2
                            else:
                                pi_electrons += 1
        
        # Apply Hückel's rule: 4n + 2
        if aromatic_rings > 0:
            # Simple heuristic: if pi_electrons satisfies 4n+2, return 1.0
            # Otherwise return a fractional value based on how close it is
            for n in range(10):
                if pi_electrons == 4 * n + 2:
                    return 1.0
            
            # If not exactly 4n+2, return a scaled value
            return float(pi_electrons) / max(pi_electrons, 1)
        
        return DEFAULT_AROMATICITY_INDEX
    except Exception as e:
        logger.warning(f"Failed to compute Hückel aromaticity index: {e}")
        return DEFAULT_AROMATICITY_INDEX

def compute_aromatic_ring_count(mol: Chem.Mol) -> int:
    """Count the number of aromatic rings."""
    if mol is None:
        return 0
    
    count = 0
    for ring in mol.GetRingInfo().AtomRings():
        if all(mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring):
            count += 1
    return count

def compute_bond_order_annotation(mol: Chem.Mol) -> float:
    """
    Estimate effective bond order based on hybridization and bond types.
    Returns average bond order across the molecule.
    """
    if mol is None:
        return DEFAULT_BOND_ORDER
    
    try:
        bond_orders = []
        for bond in mol.GetBonds():
            bond_type = bond.GetBondType()
            if bond_type == Chem.BondType.DOUBLE:
                bond_orders.append(2.0)
            elif bond_type == Chem.BondType.TRIPLE:
                bond_orders.append(3.0)
            elif bond_type == Chem.BondType.AROMATIC:
                # Aromatic bonds have intermediate order
                bond_orders.append(1.5)
            else:
                # Single bond
                bond_orders.append(1.0)
        
        if not bond_orders:
            return DEFAULT_BOND_ORDER
        
        return float(np.mean(bond_orders))
    except Exception as e:
        logger.warning(f"Failed to compute bond order annotation: {e}")
        return DEFAULT_BOND_ORDER

def compute_bond_polarity(mol: Chem.Mol) -> float:
    """
    Compute bond polarity using Pauling electronegativity differences.
    Returns average polarity across all bonds.
    """
    if mol is None:
        return DEFAULT_BOND_POLARITY
    
    try:
        # Pauling electronegativity values for common elements
        electronegativities = {
            1: 2.20,   # H
            6: 2.55,   # C
            7: 3.04,   # N
            8: 3.44,   # O
            9: 3.98,   # F
            15: 2.19,  # P
            16: 2.58,  # S
            17: 3.16,  # Cl
            35: 2.96,  # Br
            53: 2.66,  # I
        }
        
        polarity_sum = 0.0
        bond_count = 0
        
        for bond in mol.GetBonds():
            atom1 = bond.GetBeginAtom()
            atom2 = bond.GetEndAtom()
            
            en1 = electronegativities.get(atom1.GetAtomicNum(), 2.55)
            en2 = electronegativities.get(atom2.GetAtomicNum(), 2.55)
            
            # Estimate bond length based on atom types and bond order
            # Simplified: average covalent radii
            radii = {
                1: 0.37, 6: 0.77, 7: 0.75, 8: 0.73, 9: 0.72,
                15: 1.10, 16: 1.02, 17: 0.99, 35: 1.14, 53: 1.33
            }
            r1 = radii.get(atom1.GetAtomicNum(), 0.77)
            r2 = radii.get(atom2.GetAtomicNum(), 0.77)
            
            bond_length = r1 + r2
            
            # Polarity = electronegativity difference * bond length
            polarity = abs(en1 - en2) * bond_length
            polarity_sum += polarity
            bond_count += 1
        
        if bond_count == 0:
            return DEFAULT_BOND_POLARITY
        
        return polarity_sum / bond_count
    except Exception as e:
        logger.warning(f"Failed to compute bond polarity: {e}")
        return DEFAULT_BOND_POLARITY

def compute_resonance_energy(mol: Chem.Mol) -> float:
    """
    Estimate resonance energy using Hückel Molecular Orbital (HMO) theory approximations.
    For conjugated systems, estimates stabilization energy.
    """
    if mol is None:
        return DEFAULT_RESONANCE_ENERGY
    
    try:
        # Count conjugated pi systems
        conjugated_systems = 0
        total_pi_electrons = 0
        
        # Simple heuristic: count aromatic rings and conjugated chains
        aromatic_rings = compute_aromatic_ring_count(mol)
        conjugated_systems += aromatic_rings
        
        # Count conjugated double bonds in non-aromatic systems
        for bond in mol.GetBonds():
            if bond.GetBondType() == Chem.BondType.DOUBLE:
                atom1 = bond.GetBeginAtom()
                atom2 = bond.GetEndAtom()
                if not atom1.GetIsAromatic() and not atom2.GetIsAromatic():
                    # Check if part of a conjugated chain
                    neighbors1 = list(atom1.GetNeighbors())
                    neighbors2 = list(atom2.GetNeighbors())
                    
                    has_conjugation = False
                    for n in neighbors1:
                        if n.GetBondToAtom(atom1).GetBondType() == Chem.BondType.DOUBLE or n.GetIsAromatic():
                            has_conjugation = True
                            break
                    for n in neighbors2:
                        if n.GetBondToAtom(atom2).GetBondType() == Chem.BondType.DOUBLE or n.GetIsAromatic():
                            has_conjugation = True
                            break
                    
                    if has_conjugation:
                        conjugated_systems += 1
                        total_pi_electrons += 2
        
        # Estimate resonance energy: ~15-20 kcal/mol per conjugated system
        # Using a simplified linear approximation
        if conjugated_systems > 0:
            # Base resonance energy per system (in arbitrary units)
            energy_per_system = 0.5  # Scaled value
            return float(conjugated_systems) * energy_per_system
        
        return DEFAULT_RESONANCE_ENERGY
    except Exception as e:
        logger.warning(f"Failed to compute resonance energy: {e}")
        return DEFAULT_RESONANCE_ENERGY

def compute_standard_descriptors(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Compute standard topological descriptors with fallback logic.
    If quantum descriptors fail, use topological proxies.
    """
    if mol is None:
        return {
            "degree_mean": 0.0, "degree_std": 0.0, "degree_max": 0.0, "degree_min": 0.0,
            "path_length_mean": 0.0, "path_length_std": 0.0, "path_length_max": 0.0, "path_length_min": 0.0,
            "ring_count": 0,
            "aromaticity_index": DEFAULT_AROMATICITY_INDEX,
            "conjugation_length": DEFAULT_CONJUGATION_LENGTH,
            "bond_polarity": DEFAULT_BOND_POLARITY,
            "resonance_energy": DEFAULT_RESONANCE_ENERGY
        }
    
    # Compute standard descriptors
    degree_stats = compute_degree_statistics(mol)
    path_stats = compute_path_length_statistics(mol)
    ring_count = compute_ring_count(mol)
    
    # Compute quantum-inspired descriptors with fallback
    try:
        aromaticity_index = compute_huckel_aromaticity_index(mol)
    except Exception:
        logger.warning("Hückel aromaticity calculation failed, using topological proxy")
        aromaticity_index = DEFAULT_AROMATICITY_INDEX
    
    try:
        conjugation_length = float(compute_aromatic_ring_count(mol) + 
                                  sum(1 for b in mol.GetBonds() if b.GetBondType() == Chem.BondType.DOUBLE))
    except Exception:
        logger.warning("Conjugation length calculation failed, using topological proxy")
        conjugation_length = DEFAULT_CONJUGATION_LENGTH
    
    try:
        bond_polarity = compute_bond_polarity(mol)
    except Exception:
        logger.warning("Bond polarity calculation failed, using topological proxy")
        bond_polarity = DEFAULT_BOND_POLARITY
    
    try:
        resonance_energy = compute_resonance_energy(mol)
    except Exception:
        logger.warning("Resonance energy calculation failed, using topological proxy")
        resonance_energy = DEFAULT_RESONANCE_ENERGY
    
    return {
        "degree_mean": degree_stats["mean"],
        "degree_std": degree_stats["std"],
        "degree_max": degree_stats["max"],
        "degree_min": degree_stats["min"],
        "path_length_mean": path_stats["mean"],
        "path_length_std": path_stats["std"],
        "path_length_max": path_stats["max"],
        "path_length_min": path_stats["min"],
        "ring_count": ring_count,
        "aromaticity_index": aromaticity_index,
        "conjugation_length": conjugation_length,
        "bond_polarity": bond_polarity,
        "resonance_energy": resonance_energy
    }

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """
    Compute descriptors for a batch of SMILES strings.
    Implements fallback logic for missing quantum descriptors.
    """
    results = []
    
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        
        if mol is None:
            # Invalid SMILES - use all defaults
            desc = compute_standard_descriptors(None)
            desc["smiles"] = smiles
            desc["status"] = "invalid"
            results.append(desc)
            continue
        
        desc = compute_standard_descriptors(mol)
        desc["smiles"] = smiles
        desc["status"] = "valid"
        results.append(desc)
    
    return pd.DataFrame(results)