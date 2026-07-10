"""
Utility functions for molecular processing, logging, and device configuration.

This module provides:
- RDKit-based SMILES parsing and validation
- Centralized logging configuration
- CPU-only device selection for PyTorch
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

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
    sanitize: bool = True
) -> Optional[Chem.Mol]:
    """
    Parses a SMILES string into an RDKit Mol object.

    Args:
        smiles: SMILES string
        sanitize: Whether to sanitize the molecule

    Returns:
        RDKit Mol object or None if parsing fails
    """
    if not smiles or not isinstance(smiles, str):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles, sanitize=sanitize)
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
    n_bits: int = 2048
) -> Optional[torch.Tensor]:
    """
    Converts a SMILES string to an ECFP (Morgan) fingerprint.

    Args:
        smiles: SMILES string
        radius: Morgan fingerprint radius (default 2 for ECFP4)
        n_bits: Number of bits in the fingerprint

    Returns:
        PyTorch tensor of shape (n_bits,) with dtype float32, or None if failed
    """
    mol = parse_smiles(smiles)
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