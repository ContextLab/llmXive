"""
Sanitization pipeline for USPTO reaction data.

This module implements Sequential Pipeline Step 1:
1. Verify SHA256 checksum of downloaded data.
2. Remove salts and standardize molecules using RDKit.
3. Output sanitized SMILES to parquet.
"""
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
from rdkit import Chem
from rdkit.Chem import MolStandardize
from rdkit.Chem.rdmolops import RemoveHs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Path constants (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "uspto_raw.parquet"
CHECKSUM_FILE = PROJECT_ROOT / "data" / "results" / "download_checksum.txt"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "sanitized_reactions.parquet"

def calculate_sha256_file(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum() -> Tuple[bool, str]:
    """
    Verify the SHA256 checksum of the downloaded data.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not CHECKSUM_FILE.exists():
        return False, f"Checksum file not found: {CHECKSUM_FILE}"
    
    try:
        with open(CHECKSUM_FILE, 'r') as f:
            checksum_content = f.read().strip()
        
        # Check for explicit failure marker
        if "FAILED" in checksum_content:
            raise FileNotFoundError("Download failed, no data available")
        
        # Extract the actual checksum (assuming format: "checksum  filename" or just checksum)
        parts = checksum_content.split()
        if len(parts) >= 1:
            stored_checksum = parts[0]
        else:
            stored_checksum = checksum_content
        
        if not RAW_DATA_PATH.exists():
            return False, f"Raw data file not found: {RAW_DATA_PATH}"
        
        actual_checksum = calculate_sha256_file(RAW_DATA_PATH)
        
        if actual_checksum.lower() != stored_checksum.lower():
            return False, f"Checksum mismatch: Expected {stored_checksum}, got {actual_checksum}"
        
        return True, f"Checksum verified: {actual_checksum}"
        
    except FileNotFoundError as e:
        raise e
    except Exception as e:
        return False, f"Checksum verification failed: {str(e)}"

def remove_salts_and_standardize(smiles: str) -> Optional[str]:
    """
    Remove salts and standardize a molecule using RDKit.
    
    Args:
        smiles: Input SMILES string
        
    Returns:
        Standardized SMILES string or None if invalid
    """
    if not smiles or not isinstance(smiles, str):
        return None
    
    try:
        # Parse SMILES to molecule
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Remove explicit hydrogens
        mol = RemoveHs(mol)
        
        # Clean up using RDKit's standardizer
        cleaner = MolStandardize.Cleaner()
        mol = cleaner.clean(mol)
        
        # Convert back to SMILES
        standardized_smiles = Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)
        
        if not standardized_smiles:
            return None
        
        return standardized_smiles
        
    except Exception as e:
        logger.debug(f"Failed to standardize SMILES '{smiles[:50]}...': {str(e)}")
        return None

def sanitize_reactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitize a DataFrame of reactions.
    
    Args:
        df: DataFrame with 'smiles' column
        
    Returns:
        Sanitized DataFrame with standardized SMILES
    """
    logger.info(f"Starting sanitization of {len(df)} reactions")
    
    # Apply sanitization
    sanitized_smiles = df['smiles'].apply(remove_salts_and_standardize)
    
    # Create new DataFrame
    sanitized_df = df.copy()
    sanitized_df['sanitized_smiles'] = sanitized_smiles
    
    # Count successes and failures
    valid_count = sanitized_df['sanitized_smiles'].notna().sum()
    invalid_count = len(df) - valid_count
    
    logger.info(f"Sanitization complete: {valid_count} valid, {invalid_count} invalid")
    
    # Log invalid entries for debugging
    if invalid_count > 0:
        invalid_indices = sanitized_df[sanitized_df['sanitized_smiles'].isna()].index.tolist()
        logger.warning(f"Invalid entries at indices: {invalid_indices[:10]}{'...' if len(invalid_indices) > 10 else ''}")
    
    return sanitized_df

def run_sanitization_pipeline() -> Dict[str, Any]:
    """
    Run the complete sanitization pipeline.
    
    Returns:
        Dictionary with pipeline statistics
    """
    logger.info("Starting sanitization pipeline")
    start_time = datetime.now()
    
    # Step 1: Verify checksum
    logger.info("Step 1: Verifying checksum...")
    try:
        success, message = verify_checksum()
        if not success:
            raise FileNotFoundError(message)
        logger.info(f"Checksum verification: {message}")
    except FileNotFoundError as e:
        logger.error(f"Checksum verification failed: {str(e)}")
        raise
    
    # Step 2: Load raw data
    logger.info("Step 2: Loading raw data...")
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}")
    
    try:
        df = pd.read_parquet(RAW_DATA_PATH)
        logger.info(f"Loaded {len(df)} records from {RAW_DATA_PATH}")
    except Exception as e:
        logger.error(f"Failed to load raw data: {str(e)}")
        raise
    
    # Step 3: Sanitize reactions
    logger.info("Step 3: Sanitizing reactions...")
    sanitized_df = sanitize_reactions(df)
    
    # Step 4: Save output
    logger.info("Step 4: Saving sanitized data...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sanitized_df.to_parquet(OUTPUT_PATH, index=False)
    logger.info(f"Saved {len(sanitized_df)} records to {OUTPUT_PATH}")
    
    # Calculate statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    stats = {
        "total_records": len(df),
        "valid_records": sanitized_df['sanitized_smiles'].notna().sum(),
        "invalid_records": sanitized_df['sanitized_smiles'].isna().sum(),
        "output_path": str(OUTPUT_PATH),
        "duration_seconds": duration,
        "timestamp": start_time.isoformat()
    }
    
    logger.info(f"Pipeline complete in {duration:.2f} seconds")
    logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
    
    return stats

def main():
    """Main entry point for the sanitization pipeline."""
    try:
        stats = run_sanitization_pipeline()
        print(json.dumps(stats, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()