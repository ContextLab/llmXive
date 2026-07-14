"""
Data loading utilities for molecular datasets.

Provides functions to load SMILES strings and target values from files,
validate SMILES format, and iterate over data in batches.
"""
import os
import re
import math
from typing import Iterator, Tuple, List, Optional
from utils.validators import enforce_2d_only_imports

# Import RDKit (2D only - enforced by validators)
from rdkit import Chem
from rdkit.Chem import Descriptors

# Regex for basic SMILES validation (simplified)
SMILES_PATTERN = re.compile(
    r'^[A-Za-z0-9@#$%&*()\-+=\[\]{}|\\/\^~<>:]+$'
)

def validate_smiles(smiles: str) -> bool:
    """
    Validate a SMILES string.
    
    Args:
        smiles: The SMILES string to validate.
        
    Returns:
        True if the SMILES string is valid, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    
    # Basic regex check
    if not SMILES_PATTERN.match(smiles):
        return False
    
    # RDKit parsing check
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None

def iterate_smiles(filepath: str) -> Iterator[Tuple[str, float]]:
    """
    Iterate over a SMILES file, yielding (smiles, target) tuples.
    
    Args:
        filepath: Path to the SMILES file (assumed to be tab-separated 
                 with SMILES in first column and target in second).
                 
    Yields:
        Tuples of (smiles_string, target_value).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                # Skip malformed lines
                continue
            
            smiles = parts[0].strip()
            try:
                target = float(parts[1].strip())
            except ValueError:
                # Skip lines with invalid target values
                continue
            
            if validate_smiles(smiles):
                yield (smiles, target)

def load_batch(filepath: str, batch_size: int) -> List[Tuple[str, float]]:
    """
    Load a batch of SMILES strings and targets from a file.
    
    Args:
        filepath: Path to the SMILES file.
        batch_size: Number of records to load.
        
    Returns:
        List of (smiles, target) tuples.
    """
    batch = []
    for smiles, target in iterate_smiles(filepath):
        batch.append((smiles, target))
        if len(batch) >= batch_size:
            break
    return batch
