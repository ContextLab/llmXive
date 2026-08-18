import os
import re
import math
from typing import Iterator, Tuple, List, Optional
from pathlib import Path
from rdkit import Chem

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
    Validate a SMILES string using regex and RDKit parsing.
    
    Args:
        smiles: The SMILES string to validate.
        
    Returns:
        bool: True if the SMILES string is valid, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    
    # First check with regex
    if not SMILES_REGEX.match(smiles):
        return False
    
    # Then check with RDKit
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    
    return True

def iterate_smiles(filepath: Path) -> Iterator[Tuple[str, Optional[float]]]:
    """
    Iterate over a file containing SMILES strings and optional target values.
    
    Expected format: One SMILES string per line, optionally followed by a tab and a target value.
    Lines starting with '#' are treated as comments and skipped.
    Empty lines are skipped.
    Invalid SMILES strings are logged and skipped.
    
    Args:
        filepath: Path to the file containing SMILES strings.
        
    Yields:
        Tuple of (smiles_string, target_value) where target_value is float or None.
    """
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return
    
    with open(filepath, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse SMILES and optional target
            parts = line.split("\t")
            smiles = parts[0].strip()
            target = None
            
            if len(parts) > 1:
                try:
                    target = float(parts[1].strip())
                except ValueError:
                    logger.warning(f"Invalid target value at line {line_num}: {parts[1]}")
                    continue
            
            # Validate SMILES
            if not validate_smiles(smiles):
                logger.warning(f"Invalid SMILES at line {line_num}: {smiles}")
                continue
            
            yield (smiles, target)

def load_batch(filepath: Path, batch_size: int) -> List[Tuple[str, Optional[float]]]:
    """
    Load a batch of SMILES strings and target values from a file.
    
    Args:
        filepath: Path to the file containing SMILES strings.
        batch_size: Number of records to load.
        
    Returns:
        List of tuples containing (smiles_string, target_value).
    """
    batch = []
    for smiles, target in iterate_smiles(filepath):
        batch.append((smiles, target))
        if len(batch) >= batch_size:
            break
    
    return batch

def main() -> None:
    """Main entry point for testing the loader."""
    logger.info("Testing loader with sample file")
    # Example usage
    test_file = Path("data/raw/sample_smiles.txt")
    if test_file.exists():
        count = 0
        for smiles, target in iterate_smiles(test_file):
            count += 1
            if count >= 5:
                break
        logger.info(f"Loaded {count} valid SMILES strings")
    else:
        logger.warning("Sample file not found, skipping test")

if __name__ == "__main__":
    main()