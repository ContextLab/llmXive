import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict
import hashlib
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem
import numpy as np

# Configure logging
def setup_logging(level=logging.INFO):
    """
    Setup basic logging configuration.
    
    Args:
        level: Logging level.
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name.
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

def get_device():
    """
    Get the device for model training (CPU only).
    
    Returns:
        String 'cpu'.
    """
    return 'cpu'

def parse_smiles(smiles: str) -> Optional[Chem.Mol]:
    """
    Parse a SMILES string into an RDKit molecule.
    
    Args:
        smiles: SMILES string.
        
    Returns:
        RDKit Mol object or None if invalid.
    """
    if not smiles or not isinstance(smiles, str):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol
    except Exception:
        return None

def validate_molecule(smiles: str) -> bool:
    """
    Validate a SMILES string.
    
    Args:
        smiles: SMILES string.
        
    Returns:
        True if valid, False otherwise.
    """
    mol = parse_smiles(smiles)
    return mol is not None

def smiles_to_ecfp(smiles: str, radius: int = 2, nBits: int = 2048) -> np.ndarray:
    """
    Convert SMILES to ECFP fingerprint.
    
    Args:
        smiles: SMILES string.
        radius: Radius of the fingerprint.
        nBits: Number of bits.
        
    Returns:
        Numpy array of fingerprint bits.
    """
    mol = parse_smiles(smiles)
    if mol is None:
        return np.zeros(nBits, dtype=int)
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nBits)
    arr = np.zeros((nBits,), dtype=int)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def clear_mol_cache():
    """
    Clear RDKit molecule cache.
    """
    Chem.ClearMolBlockCache()

def get_cache_stats() -> Dict:
    """
    Get RDKit cache statistics.
    
    Returns:
        Dictionary of cache stats.
    """
    return {
        "cache_size": Chem.GetMolBlockCacheSize()
    }
