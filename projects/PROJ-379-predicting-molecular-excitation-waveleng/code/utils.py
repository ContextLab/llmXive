"""
Utility functions for molecular processing, logging, and device configuration.

This module provides:
- RDKit-based SMILES parsing and validation
- Centralized logging configuration
- CPU-only device selection for PyTorch
- Caching for RDKit molecule objects to optimize graph construction
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict
import hashlib

import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem
import torch

# Configure RDKit to suppress warnings
rdkit.RDLogger.DisableLog('rdApp.*')

# Project root (assumes code/ is at project root or one level up)
# Adjust if running from a subdirectory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Cache for RDKit molecules: maps SMILES hash to Mol object
_mol_cache: Dict[str, Chem.Mol] = {}
_cache_max_size = 10000  # Limit cache size to prevent memory bloat

def _get_smiles_hash(smiles: str) -> str:
    """Generate a hash for a SMILES string for caching."""
    return hashlib.md5(smiles.encode('utf-8')).hexdigest()

def get_device() -> torch.device:
    """
    Returns a CPU-only device as required by project constraints.
    GPU usage is explicitly disabled.
    """
    return torch.device("cpu")

def setup_logging(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Configures and returns a logger with file and/or console handlers.

    Args:
        name: Logger name (typically __name__)
        log_file: Relative path to log file (e.g., "ingest.log")
        level: Logging level
        console: Whether to log to stdout

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    if log_file:
        log_path = LOGS_DIR / log_file
        fh = logging.FileHandler(log_path)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Console handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

def parse_smiles(
    smiles: str,
    sanitize: bool = True,
    use_cache: bool = True
) -> Optional[Chem.Mol]:
    """
    Parses a SMILES string into an RDKit Mol object.
    
    Includes an optional caching mechanism to avoid redundant parsing
    of identical SMILES strings, optimizing graph construction.

    Args:
        smiles: SMILES string
        sanitize: Whether to sanitize the molecule
        use_cache: Whether to use the internal cache

    Returns:
        RDKit Mol object or None if parsing fails
    """
    if not smiles or not isinstance(smiles, str):
        return None
    
    if use_cache:
        # Normalize SMILES (remove whitespace)
        norm_smiles = smiles.strip()
        cache_key = _get_smiles_hash(norm_smiles)
        
        if cache_key in _mol_cache:
            return _mol_cache[cache_key]
    
    try:
        mol = Chem.MolFromSmiles(smiles, sanitize=sanitize)
        
        if use_cache and mol is not None:
            # Manage cache size
            if len(_mol_cache) >= _cache_max_size:
                # Simple eviction: clear oldest half (approx)
                # In production, a more sophisticated LRU might be used
                keys_to_remove = list(_mol_cache.keys())[:len(_mol_cache)//2]
                for k in keys_to_remove:
                    del _mol_cache[k]
            
            _mol_cache[cache_key] = mol
        
        return mol
    except Exception:
        return None

def validate_molecule(
    mol: Optional[Chem.Mol]
) -> Tuple[bool, str]:
    """
    Validates an RDKit molecule object.

    Checks:
    - Object is not None
    - Has at least one atom
    - Has at least one bond (unless it's a single atom like [He])

    Args:
        mol: RDKit Mol object

    Returns:
        Tuple of (is_valid, reason)
    """
    if mol is None:
        return False, "Molecule is None"

    if mol.GetNumAtoms() == 0:
        return False, "Molecule has no atoms"

    # Allow single atoms (e.g., noble gases)
    if mol.GetNumBonds() == 0 and mol.GetNumAtoms() > 1:
        return False, "Molecule has no bonds but has multiple atoms"

    return True, "Valid"

def smiles_to_ecfp(
    smiles: str,
    radius: int = 2,
    n_bits: int = 2048,
    use_cache: bool = True
) -> Optional[torch.Tensor]:
    """
    Converts a SMILES string to an ECFP (Morgan) fingerprint.
    
    Optimized to reuse cached RDKit molecule objects if available.

    Args:
        smiles: SMILES string
        radius: Morgan fingerprint radius (default 2 for ECFP4)
        n_bits: Number of bits in the fingerprint
        use_cache: Whether to use the internal molecule cache

    Returns:
        PyTorch tensor of shape (n_bits,) with dtype float32, or None if failed
    """
    # Use cached molecule if available to avoid re-parsing
    mol = parse_smiles(smiles, use_cache=use_cache)
    if mol is None:
        return None

    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = [0] * n_bits
    for idx in fp.GetOnBits():
        arr[idx] = 1
    return torch.tensor(arr, dtype=torch.float32)

def get_logger() -> logging.Logger:
    """
    Convenience function to get a default logger for this module.
    """
    return setup_logging(__name__, log_file="utils.log", console=True)

def clear_mol_cache() -> int:
    """
    Clears the molecule cache.
    Returns the number of items cleared.
    """
    count = len(_mol_cache)
    _mol_cache.clear()
    return count

def get_cache_stats() -> Dict[str, int]:
    """
    Returns statistics about the current molecule cache.
    """
    return {
        "cache_size": len(_mol_cache),
        "max_size": _cache_max_size
    }