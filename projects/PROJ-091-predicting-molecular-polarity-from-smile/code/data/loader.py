import os
import re
import math
from typing import Iterator, Tuple, List, Optional
from pathlib import Path

from rdkit import Chem
from utils.validators import enforce_2d_only_imports
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Comprehensive SMILES validation regex
# Matches valid SMILES characters including atoms, bonds, branches, rings, charges, isotopes, and stereochemistry
# Excludes whitespace and control characters
SMILES_REGEX = re.compile(
    r'^[A-Za-z0-9@#$%&*()\-+=\[\]{}\\\/\|~^!;<>:]+$'
)

def validate_smiles(smiles: str) -> bool:
    """
    Validate SMILES string format using regex and RDKit.
    
    First performs a regex check for valid SMILES characters, then uses RDKit
    to ensure the string can be parsed into a valid molecule.
    
    Args:
        smiles: The SMILES string to validate.
        
    Returns:
        bool: True if the SMILES string is valid (passes regex and RDKit parsing), False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    
    # Regex validation
    if not SMILES_REGEX.match(smiles):
        return False
    
    # RDKit validation
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def iterate_smiles(filepath: Path) -> Iterator[Tuple[str, float]]:
    """
    Iterate over SMILES and target values from a file.
    
    Yields tuples of (smiles, target) for valid entries.
    Invalid SMILES strings are logged and skipped.
    
    Args:
        filepath: Path to the file containing SMILES and target values.
        
    Yields:
        Tuple[str, float]: A tuple of SMILES string and target value.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    valid_count = 0
    invalid_count = 0
    
    with open(filepath, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                smiles = parts[0]
                try:
                    target = float(parts[1])
                    if validate_smiles(smiles):
                        valid_count += 1
                        yield smiles, target
                    else:
                        invalid_count += 1
                        logger.warning(f"Invalid SMILES at line {line_num}: {smiles}")
                except ValueError:
                    invalid_count += 1
                    logger.warning(f"Invalid target value at line {line_num}: {parts[1]}")
    
    logger.info(f"Loaded {valid_count} valid entries, skipped {invalid_count} invalid entries")

def load_batch(filepath: Path, batch_size: int) -> Iterator[List[Tuple[str, float]]]:
    """
    Load batches of SMILES and targets from a file.
    
    Args:
        filepath: Path to the file containing SMILES and target values.
        batch_size: Number of entries per batch.
        
    Yields:
        List[Tuple[str, float]]: A list of (smiles, target) tuples.
    """
    batch = []
    for smiles, target in iterate_smiles(filepath):
        batch.append((smiles, target))
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def main() -> None:
    """Main entry point for testing loader."""
    # This is a placeholder; actual usage would require a real file
    logger.info("Loader module loaded successfully")

if __name__ == "__main__":
    main()