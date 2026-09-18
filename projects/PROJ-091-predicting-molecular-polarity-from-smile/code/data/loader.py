import os
import re
import math
from typing import Iterator, Tuple, List, Optional
from pathlib import Path
from rdkit import Chem
import logging
import csv
import gzip
import io

from utils.logging_config import get_logger

logger = get_logger(__name__)

# SMILES validation regex (simplified but robust for common organic molecules)
SMILES_REGEX = re.compile(r'^[CNOcnsSFPBrIcl1234567890=\[\]().-]+$')

def validate_smiles(smiles: str) -> bool:
    """Validate a SMILES string using regex and RDKit."""
    if not smiles or not isinstance(smiles, str):
        return False
    # Quick regex check first
    if not SMILES_REGEX.match(smiles):
        return False
    # RDKit check
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None

def iterate_smiles(filepath: Path) -> Iterator[Tuple[str, float]]:
    """
    Iterate over a CSV file containing SMILES and target values.
    Supports both .csv and .csv.gz formats.
    Yields (smiles, target) tuples.
    
    Args:
        filepath: Path to the CSV or CSV.GZ file.
        
    Yields:
        Tuple of (smiles_string, target_float)
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid or target cannot be parsed.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Determine if gzipped
    is_gzipped = str(filepath).endswith('.gz')
    
    try:
        # Open file with appropriate handler
        if is_gzipped:
            f_handle = gzip.open(filepath, 'rt', encoding='utf-8')
        else:
            f_handle = open(filepath, 'r', encoding='utf-8')
        
        with f_handle as f:
            # Read header
            header_line = f.readline()
            if not header_line:
                raise ValueError("Empty file or missing header")
            
            header = header_line.strip().split(',')
            
            # Find indices for 'smiles' and 'target' (or 'dipole_moment')
            # Normalize column names to lowercase for matching
            header_lower = [h.strip().lower() for h in header]
            
            smiles_idx = None
            target_idx = None
            
            # Look for 'smiles'
            if 'smiles' in header_lower:
                smiles_idx = header_lower.index('smiles')
            elif 'smile' in header_lower:
                smiles_idx = header_lower.index('smile')
                
            # Look for target (dipole moment)
            if 'target' in header_lower:
                target_idx = header_lower.index('target')
            elif 'dipole_moment' in header_lower:
                target_idx = header_lower.index('dipole_moment')
            
            if smiles_idx is None:
                raise ValueError("No 'smiles' column found in header")
            if target_idx is None:
                raise ValueError("No 'target' or 'dipole_moment' column found in header")
            
            for line_num, line in enumerate(f, start=2):
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split(',')
                
                if len(parts) <= max(smiles_idx, target_idx):
                    logger.warning(f"Skipping malformed line {line_num}: {line}")
                    continue
                    
                smiles = parts[smiles_idx].strip()
                target_str = parts[target_idx].strip()
                
                try:
                    target = float(target_str)
                except ValueError:
                    logger.warning(f"Invalid target value on line {line_num}: {target_str}")
                    continue
                
                if not validate_smiles(smiles):
                    logger.warning(f"Invalid SMILES on line {line_num}: {smiles}")
                    continue
                    
                yield smiles, target
                
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        raise

def load_batch(filepath: Path, batch_size: int) -> Iterator[Tuple[List[str], List[float]]]:
    """
    Load data in batches from a CSV file.
    Supports both .csv and .csv.gz formats.
    
    Args:
        filepath: Path to the CSV or CSV.GZ file.
        batch_size: Number of records per batch.
        
    Yields:
        Tuple of (list_of_smiles, list_of_targets)
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
        
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    smiles_batch = []
    target_batch = []

    try:
        for smiles, target in iterate_smiles(filepath):
            smiles_batch.append(smiles)
            target_batch.append(target)

            if len(smiles_batch) >= batch_size:
                yield smiles_batch, target_batch
                smiles_batch = []
                target_batch = []

        if smiles_batch:
            yield smiles_batch, target_batch
    except Exception as e:
        logger.error(f"Error loading batch from {filepath}: {e}")
        raise

def main():
    """Main entry point for testing loader."""
    # Example usage
    test_file = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "qm9_smiles.csv.gz"
    if test_file.exists():
        logger.info(f"Testing loader on {test_file}")
        count = 0
        try:
            for smiles, target in iterate_smiles(test_file):
                count += 1
                if count >= 10:
                    break
            logger.info(f"Successfully loaded {count} samples.")
        except Exception as e:
            logger.error(f"Loader test failed: {e}")
    else:
        logger.warning(f"Test file not found: {test_file}")

if __name__ == "__main__":
    main()