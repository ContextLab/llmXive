"""
Sanitization module for USPTO reaction data.

Implements:
1. Checksum verification against downloaded artifact.
2. Salt removal and standardization using RDKit.
3. Yield parsing (ranges vs single values).
4. Output of sanitized SMILES and processed data.
"""
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Iterator

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolStandardize
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem import rdmolops

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_PATH = Path("data/raw/uspto_raw.parquet")
CHECKSUM_PATH = Path("data/results/download_checksum.txt")
SANITIZED_OUTPUT_PATH = Path("data/processed/sanitized_reactions.parquet")
EXCLUSION_LOG_PATH = Path("data/results/sanitize_exclusions.json")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum() -> bool:
    """
    Verify that the downloaded file's checksum matches the recorded checksum.
    Returns True if match, raises ValueError if mismatch or files missing.
    """
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}")
    
    if not CHECKSUM_PATH.exists():
        raise FileNotFoundError(f"Checksum file not found: {CHECKSUM_PATH}")

    recorded_checksum = CHECKSUM_PATH.read_text().strip()
    current_checksum = calculate_sha256(RAW_DATA_PATH)

    if recorded_checksum != current_checksum:
        raise ValueError(
            f"Checksum mismatch!\n"
            f"Recorded: {recorded_checksum}\n"
            f"Current:  {current_checksum}\n"
            f"File: {RAW_DATA_PATH}"
        )
    
    logger.info(f"Checksum verified successfully: {current_checksum}")
    return True

def remove_salts_and_standardize(smiles: str) -> Optional[str]:
    """
    Remove salts and standardize a SMILES string using RDKit.
    
    Steps:
    1. Convert SMILES to Mol
    2. Use MolStandardize.Cleaner to remove salts
    3. Remove explicit hydrogens
    4. Return canonical SMILES
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.debug(f"Failed to parse SMILES: {smiles}")
            return None

        # Standardize: remove salts
        # Using the MolStandardize pipeline
        cleaner = rdMolStandardize.Cleaner()
        mol = cleaner.clean(mol)

        # Remove explicit hydrogens
        mol = rdmolops.RemoveHs(mol)

        if mol is None or mol.GetNumAtoms() == 0:
            return None

        # Return canonical SMILES
        return Chem.MolToSmiles(mol, isomericSmiles=True)
    except Exception as e:
        logger.debug(f"Standardization failed for {smiles}: {e}")
        return None

def parse_yield(yield_val) -> Optional[float]:
    """
    Parse yield value. Handles ranges (e.g., "50-60%") and single values.
    Returns midpoint for ranges, float for single values.
    Returns None if unparseable.
    """
    if yield_val is None:
        return None

    val_str = str(yield_val).strip()
    
    # Handle range format "50-60%" or "50 - 60"
    if '-' in val_str:
        try:
            parts = val_str.replace('%', '').split('-')
            if len(parts) == 2:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return (low + high) / 2.0
        except ValueError:
            pass
    
    # Handle single value with %
    try:
        clean_val = val_str.replace('%', '').strip()
        return float(clean_val)
    except ValueError:
        return None

def sanitize_reactions() -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Main sanitization pipeline.
    
    1. Verify checksum.
    2. Load raw parquet.
    3. Sanitize SMILES (salt removal, standardization).
    4. Parse yields.
    5. Filter invalid entries.
    6. Save results and exclusion log.
    """
    # Step 1: Verify Checksum
    logger.info("Starting checksum verification...")
    verify_checksum()

    # Step 2: Load Data
    logger.info(f"Loading raw data from {RAW_DATA_PATH}...")
    try:
        df = pd.read_parquet(RAW_DATA_PATH)
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet file: {e}")

    logger.info(f"Loaded {len(df)} rows.")

    exclusion_reasons = {
        "invalid_smiles": 0,
        "empty_mol": 0,
        "invalid_yield": 0,
        "missing_smiles": 0,
        "missing_yield": 0
    }

    def process_row(row: pd.Series) -> Optional[Dict[str, Any]]:
        # Check SMILES
        smiles = row.get('smiles')
        if pd.isna(smiles) or not isinstance(smiles, str) or not smiles.strip():
            exclusion_reasons["missing_smiles"] += 1
            return None

        # Sanitize SMILES
        sanitized_smiles = remove_salts_and_standardize(smiles)
        if sanitized_smiles is None:
            exclusion_reasons["invalid_smiles"] += 1
            return None

        # Check Yield
        yield_val = row.get('yield')
        if pd.isna(yield_val):
            exclusion_reasons["missing_yield"] += 1
            return None

        parsed_yield = parse_yield(yield_val)
        if parsed_yield is None:
            exclusion_reasons["invalid_yield"] += 1
            return None

        return {
            'smiles': sanitized_smiles,
            'yield': parsed_yield,
            'reaction_class': row.get('reaction_class', 'unknown')
        }

    logger.info("Sanitizing reactions...")
    results = []
    
    # Process in chunks to manage memory if needed, though map is usually fine
    for idx, row in df.iterrows():
        res = process_row(row)
        if res:
            results.append(res)

    sanitized_df = pd.DataFrame(results)
    
    # Calculate exclusion stats
    total_input = len(df)
    total_output = len(sanitized_df)
    total_excluded = total_input - total_output
    
    exclusion_stats = {
        "total_input_rows": total_input,
        "total_output_rows": total_output,
        "total_excluded_rows": total_excluded,
        "exclusion_fraction": total_excluded / total_input if total_input > 0 else 0.0,
        "reasons": exclusion_reasons
    }

    # Save sanitized data
    SANITIZED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sanitized_df.to_parquet(SANITIZED_OUTPUT_PATH, index=False)
    logger.info(f"Saved sanitized data to {SANITIZED_OUTPUT_PATH}")

    # Save exclusion log
    EXCLUSION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EXCLUSION_LOG_PATH, 'w') as f:
        json.dump(exclusion_stats, f, indent=2)
    logger.info(f"Saved exclusion log to {EXCLUSION_LOG_PATH}")

    return sanitized_df, exclusion_stats

def main():
    """Entry point for the sanitize script."""
    logger.info("=== Starting Sanitization Pipeline ===")
    start_time = datetime.now()
    
    try:
        df, stats = sanitize_reactions()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
        logger.info(f"Exclusion Fraction: {stats['exclusion_fraction']:.4f}")
        logger.info(f"Reasons: {stats['reasons']}")
        
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())