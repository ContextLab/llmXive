"""
Sanitize chemical structures and parse yield values.

Steps:
1. Verify checksum (if provided)
2. Remove salts using RDKit
3. Standardize SMILES (remove Hs, canonicalize)
4. Parse yield values (handle ranges, exclude unparseable)
"""
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import MolStandardize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/sanitize.log')
    ]
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum_path: str) -> bool:
    """Verify file checksum against expected value."""
    if not Path(expected_checksum_path).exists():
        logger.warning(f"Checksum file not found: {expected_checksum_path}")
        return True
    
    with open(expected_checksum_path, 'r') as f:
        expected_hash = f.read().strip()
    
    actual_hash = calculate_sha256(file_path)
    if actual_hash != expected_hash:
        logger.error(f"Checksum mismatch for {file_path}")
        logger.error(f"Expected: {expected_hash}")
        logger.error(f"Actual: {actual_hash}")
        return False
    
    logger.info(f"Checksum verified for {file_path}")
    return True

def remove_salts(smiles: str) -> Optional[str]:
    """Remove salts and counterions from a SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Use RDKit's salt remover
        cleaner = MolStandardize.cleaner.Cleaner()
        mol_clean = cleaner.clean(mol)
        
        if mol_clean is None:
            return None
        
        # Remove explicit hydrogens
        mol_no_h = Chem.RemoveHs(mol_clean)
        
        return Chem.MolToSmiles(mol_no_h, isomericSmiles=True)
    except Exception as e:
        logger.debug(f"Failed to remove salts from {smiles}: {e}")
        return None

def standardize_smiles(smiles: str) -> Optional[str]:
    """Standardize a SMILES string (canonicalize, remove Hs)."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        mol_no_h = Chem.RemoveHs(mol)
        return Chem.MolToSmiles(mol_no_h, isomericSmiles=True)
    except Exception as e:
        logger.debug(f"Failed to standardize SMILES {smiles}: {e}")
        return None

def parse_yield(yield_val) -> Optional[float]:
    """
    Parse yield value, handling ranges and various formats.
    
    - "50-60%" -> 55.0
    - "50%" -> 50.0
    - 50.0 -> 50.0
    - "N/A", "unknown" -> None
    """
    if yield_val is None:
        return None
    
    if isinstance(yield_val, (int, float)):
        if 0.0 <= yield_val <= 100.0:
            return float(yield_val)
        return None
    
    if not isinstance(yield_val, str):
        return None
    
    yield_str = yield_val.strip().lower()
    
    if yield_str in ['n/a', 'unknown', 'none', '']:
        return None
    
    # Handle range: "50-60%" or "50 - 60 %"
    if '-' in yield_str:
        parts = yield_str.replace('%', '').split('-')
        if len(parts) == 2:
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                if 0.0 <= low <= 100.0 and 0.0 <= high <= 100.0:
                    return (low + high) / 2.0
            except ValueError:
                pass
        return None
    
    # Handle single value: "50%" or "50"
    yield_str = yield_str.replace('%', '').strip()
    try:
        val = float(yield_str)
        if 0.0 <= val <= 100.0:
            return val
    except ValueError:
        pass
    
    return None

def sanitize_reactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Sanitize a DataFrame of reactions.
    
    Steps:
    1. Clean SMILES (remove salts, standardize)
    2. Parse yield values
    3. Filter out invalid entries
    
    Returns:
        Tuple of (cleaned DataFrame, list of exclusion reasons)
    """
    exclusion_log = []
    valid_indices = []
    
    logger.info(f"Sanitizing {len(df)} reactions...")
    
    for idx, row in df.iterrows():
        reasons = []
        
        # Check SMILES
        smiles = row.get('smiles', '')
        if not smiles or not isinstance(smiles, str):
            reasons.append("Invalid or missing SMILES")
        
        if not reasons:
            # Remove salts and standardize
            clean_smiles = remove_salts(smiles)
            if clean_smiles is None:
                reasons.append("Failed to clean SMILES")
            else:
                # Standardize
                std_smiles = standardize_smiles(clean_smiles)
                if std_smiles is None:
                    reasons.append("Failed to standardize SMILES")
                else:
                    # Parse yield
                    yield_val = row.get('yield', None)
                    parsed_yield = parse_yield(yield_val)
                    if parsed_yield is None:
                        reasons.append("Failed to parse yield")
                    else:
                        # Valid row
                        valid_indices.append(idx)
                        continue
        
        if reasons:
            exclusion_log.append({
                "index": idx,
                "reasons": reasons,
                "original_smiles": smiles,
                "original_yield": str(row.get('yield', ''))
            })
    
    logger.info(f"Excluded {len(exclusion_log)} rows")
    
    if len(valid_indices) == 0:
        raise ValueError("No valid rows after sanitization")
    
    df_clean = df.iloc[valid_indices].copy()
    
    # Update SMILES and yield columns
    df_clean['smiles'] = df_clean['smiles'].apply(lambda x: standardize_smiles(remove_salts(x)) if x else None)
    df_clean['yield'] = df_clean['yield'].apply(parse_yield)
    
    # Drop rows where sanitization failed (should be none if logic is correct)
    df_clean = df_clean.dropna(subset=['smiles', 'yield'])
    
    return df_clean, exclusion_log

def main():
    """Entry point for sanitization script."""
    logger.info("Starting sanitization (T014/T015)...")
    
    try:
        # This is a helper function, not a full script
        # The full pipeline is run by ingest.py
        logger.info("Sanitization functions ready. Run ingest.py for full pipeline.")
    except Exception as e:
        logger.error(f"Sanitization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
