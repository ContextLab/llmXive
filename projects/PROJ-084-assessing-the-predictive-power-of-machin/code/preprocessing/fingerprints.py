"""
Fingerprint generation module for molecular structures.

Provides functions to generate ECFP4 and MACCS fingerprints from RDKit Mol objects.
"""
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs
import numpy as np
from typing import Union


def generate_ecfp4(mol: Chem.Mol, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generate ECFP4 (Extended Connectivity Fingerprint with radius 2) for a molecule.
    
    Args:
        mol: RDKit Mol object
        radius: Radius of the fingerprint (2 for ECFP4)
        n_bits: Number of bits in the fingerprint (default 2048)
    
    Returns:
        numpy array of shape (n_bits,) containing the fingerprint
    """
    if mol is None:
        raise ValueError("Input molecule is None")
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=int)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def generate_maccs(mol: Chem.Mol) -> np.ndarray:
    """
    Generate MACCS keys fingerprint for a molecule.
    
    Args:
        mol: RDKit Mol object
    
    Returns:
        numpy array of shape (167,) containing the MACCS fingerprint
    """
    if mol is None:
        raise ValueError("Input molecule is None")
    
    fp = MACCSkeys.GenMACCSKeys(mol)
    arr = np.zeros((167,), dtype=int)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def generate_fingerprints_batch(
    mols: list[Chem.Mol],
    fingerprint_type: str = "ecfp4"
) -> np.ndarray:
    """
    Generate fingerprints for a batch of molecules.
    
    Args:
        mols: List of RDKit Mol objects
        fingerprint_type: Type of fingerprint ('ecfp4' or 'maccs')
    
    Returns:
        numpy array of shape (n_molecules, n_bits)
    """
    if fingerprint_type == "ecfp4":
        fps = [generate_ecfp4(mol) for mol in mols]
    elif fingerprint_type == "maccs":
        fps = [generate_maccs(mol) for mol in mols]
    else:
        raise ValueError(f"Unknown fingerprint type: {fingerprint_type}")
    
    return np.vstack(fps) if fps else np.array([])
