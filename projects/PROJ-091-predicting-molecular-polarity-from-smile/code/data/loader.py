import os
import re
import math
from typing import Iterator, Tuple, List, Optional
from pathlib import Path
from rdkit import Chem
import logging

from utils.logging_config import get_logger

logger = get_logger(__name__)

# SMILES validation regex (simplified)
SMILES_REGEX = re.compile(r'^[CNOcnsSFPBrIcl1234567890=\[\]().-]+$')

def validate_smiles(smiles: str) -> bool:
    """Validate a SMILES string using regex and RDKit."""
    if not smiles or not isinstance(smiles, str):
        return False
    if not SMILES_REGEX.match(smiles):
        return False
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None

def iterate_smiles(filepath: Path) -> Iterator[Tuple[str, float]]:
    """
    Iterate over a CSV file containing SMILES and target values.
    Yields (smiles, target) tuples.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            header = f.readline().strip().split(',')
            smiles_idx = header.index('smiles') if 'smiles' in header else 0
            target_idx = header.index('target') if 'target' in header else 1

            for line_num, line in enumerate(f, start=2):
                parts = line.strip().split(',')
                if len(parts) <= max(smiles_idx, target_idx):
                    logger.warning(f"Skipping malformed line {line_num}: {line}")
                    continue
                smiles = parts[smiles_idx]
                try:
                    target = float(parts[target_idx])
                except ValueError:
                    logger.warning(f"Invalid target value on line {line_num}: {parts[target_idx]}")
                    continue

                if validate_smiles(smiles):
                    yield smiles, target
                else:
                    logger.warning(f"Invalid SMILES on line {line_num}: {smiles}")
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        raise

def load_batch(filepath: Path, batch_size: int) -> Iterator[Tuple[List[str], List[float]]]:
    """
    Load data in batches.
    Yields (list_of_smiles, list_of_targets) tuples.
    """
    smiles_batch = []
    target_batch = []

    for smiles, target in iterate_smiles(filepath):
        smiles_batch.append(smiles)
        target_batch.append(target)

        if len(smiles_batch) >= batch_size:
            yield smiles_batch, target_batch
            smiles_batch = []
            target_batch = []

    if smiles_batch:
        yield smiles_batch, target_batch

def main():
    """Main entry point for testing loader."""
    # Example usage
    test_file = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "qm9_smiles.csv.gz"
    if test_file.exists():
        logger.info(f"Testing loader on {test_file}")
        count = 0
        for smiles, target in iterate_smiles(test_file):
            count += 1
            if count >= 10:
                break
        logger.info(f"Successfully loaded {count} samples.")
    else:
        logger.warning(f"Test file not found: {test_file}")

if __name__ == "__main__":
    main()
