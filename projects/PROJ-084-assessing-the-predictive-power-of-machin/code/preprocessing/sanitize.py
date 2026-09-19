"""
Sanitization utilities for chemical data.
Implements T014: Load raw data, verify checksum, remove salts, standardize SMILES.
"""
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union, Iterator, Dict, Any

import pandas as pd
from rdkit import Chem
from rdkit.Chem import MolStandardize

# Import path constants from config
try:
    from config import DATA_RAW_DIR, DATA_RESULTS_DIR
except ImportError:
    # Fallback for standalone execution if config is not in path
    from pathlib import Path
    DATA_RAW_DIR = Path("data/raw")
    DATA_RESULTS_DIR = Path("data/results")

logger = logging.getLogger(__name__)

# Constants for T014
RAW_DATA_FILE = DATA_RAW_DIR / "uspto_raw.parquet"
CHECKSUM_FILE = DATA_RESULTS_DIR / "download_checksum.txt"
SANITIZED_OUTPUT_FILE = DATA_RAW_DIR / "uspto_sanitized.parquet"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def verify_checksum(file_path: Path, checksum_file: Path) -> bool:
    """
    Verify the SHA256 checksum of file_path against the stored value in checksum_file.
    
    Returns:
        True if checksums match and no failure marker is present.
        False if checksum file is missing or checksums do not match.
    """
    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        return False
    
    with open(checksum_file, 'r') as f:
        content = f.read().strip()
    
    # Check for explicit failure marker as per T014 requirement
    if "FAILED" in content:
        logger.error("Download failed, no data available.")
        raise FileNotFoundError("Download failed, no data available")
    
    # Expected format: "checksum  filename" or just "checksum"
    stored_checksum = content.split()[0] if content else ""
    
    if not stored_checksum:
        logger.error(f"Could not parse checksum from {checksum_file}")
        return False
    
    calc_checksum = calculate_sha256(file_path)
    logger.info(f"Stored checksum: {stored_checksum}")
    logger.info(f"Calculated checksum: {calc_checksum}")
    
    return stored_checksum == calc_checksum

def remove_salts_and_standardize(smiles: str) -> Optional[str]:
    """
    Remove salts and standardize a SMILES string using RDKit.
    
    Steps:
    1. Parse SMILES to Mol
    2. Clean using MolStandardize.Cleaner()
    3. Remove explicit Hydrogens
    4. Convert back to canonical SMILES
    
    Args:
        smiles: Input SMILES string
        
    Returns:
        Sanitized canonical SMILES or None if parsing fails
    """
    if not smiles or not isinstance(smiles, str):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Standardize: remove salts, normalize, etc.
        cleaner = MolStandardize.Cleaner()
        mol = cleaner.clean(mol)
        
        # Remove explicit hydrogens
        mol = Chem.RemoveHs(mol)
        
        # Convert to canonical SMILES
        return Chem.MolToSmiles(mol, isomericSmiles=True)
    except Exception as e:
        logger.debug(f"Failed to sanitize SMILES: {smiles} -> {e}")
        return None

def sanitize_reactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply sanitization to a batch of reactions.
    
    Args:
        df: DataFrame with 'smiles' column
        
    Returns:
        DataFrame with sanitized 'smiles' column
    """
    logger.info(f"Sanitizing {len(df)} reactions...")
    df['smiles'] = df['smiles'].apply(remove_salts_and_standardize)
    
    # Log statistics
    valid_count = df['smiles'].notna().sum()
    invalid_count = len(df) - valid_count
    logger.info(f"Sanitization complete: {valid_count} valid, {invalid_count} invalid")
    
    return df

def parse_yield_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for yield parsing logic.
    Yield parsing is handled in ingest.py (T015).
    This function is kept for compatibility.
    """
    return df

def run_sanitization_pipeline():
    """
    Main pipeline for T014:
    1. Verify checksum of raw data
    2. Load raw data
    3. Sanitize SMILES
    4. Save sanitized data
    """
    start_time = datetime.now()
    logger.info(f"Starting sanitization pipeline at {start_time}")
    
    # Step 1: Verify checksum
    logger.info(f"Verifying checksum for {RAW_DATA_FILE}")
    if not RAW_DATA_FILE.exists():
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_FILE}")
    
    # This will raise FileNotFoundError if checksum contains "FAILED"
    # or return False if checksum mismatch
    if not verify_checksum(RAW_DATA_FILE, CHECKSUM_FILE):
        raise ValueError("Checksum verification failed. Raw data may be corrupted.")
    
    # Step 2: Load raw data
    logger.info(f"Loading raw data from {RAW_DATA_FILE}")
    try:
        df = pd.read_parquet(RAW_DATA_FILE)
        logger.info(f"Loaded {len(df)} rows")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise
    
    # Step 3: Sanitize
    df_sanitized = sanitize_reactions(df)
    
    # Step 4: Save output
    # Ensure output directory exists
    SANITIZED_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving sanitized data to {SANITIZED_OUTPUT_FILE}")
    df_sanitized.to_parquet(SANITIZED_OUTPUT_FILE, index=False)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Sanitization pipeline completed in {duration:.2f} seconds")
    logger.info(f"Output saved to {SANITIZED_OUTPUT_FILE}")
    
    return df_sanitized

def main():
    """Entry point for running sanitization."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        df = run_sanitization_pipeline()
        logger.info("Sanitization completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()