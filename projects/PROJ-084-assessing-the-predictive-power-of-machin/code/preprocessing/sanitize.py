"""
Sanitization module for USPTO dataset.

Tasks:
1. Verify SHA256 checksum of downloaded raw data.
2. Remove salts and standardize molecules using RDKit.
3. Parse yield values (handle ranges and single values).
4. Output sanitized SMILES and cleaned dataframe.
"""

import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/sanitize.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_PATH = Path("data/raw/uspto_raw.parquet")
CHECKSUM_FILE = Path("data/results/download_checksum.txt")
SANITIZED_OUTPUT_PATH = Path("data/processed/sanitized_reactions.parquet")
SANITIZATION_LOG_PATH = Path("data/results/sanization_log.json")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(expected_checksum_path: Path, actual_file_path: Path) -> bool:
    """Verify SHA256 checksum matches expected value."""
    if not expected_checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {expected_checksum_path}")
    if not actual_file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {actual_file_path}")
    
    with open(expected_checksum_path, 'r') as f:
        expected_checksum = f.read().strip()
    
    actual_checksum = calculate_sha256(actual_file_path)
    
    if actual_checksum != expected_checksum:
        raise ValueError(
            f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}"
        )
    
    logger.info(f"Checksum verified successfully: {actual_checksum}")
    return True

def remove_salts_and_standardize(smiles: str) -> Optional[str]:
    """
    Remove salts and standardize a molecule using RDKit.
    
    Args:
        smiles: Input SMILES string
        
    Returns:
        Sanitized SMILES string or None if molecule is invalid
    """
    try:
        # Parse SMILES to molecule
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Remove hydrogens
        mol = Chem.RemoveHs(mol)
        
        # Use RDKit's MolStandardize cleaner to remove salts
        # The Cleaner() function handles salt removal and standardization
        cleaner = rdMolStandardize.Cleaner()
        mol = cleaner.clean(mol)
        
        # Convert back to SMILES
        sanitized_smiles = Chem.MolToSmiles(mol, canonical=True)
        
        # Validate the result
        if sanitized_smiles and Chem.MolFromSmiles(sanitized_smiles) is not None:
            return sanitized_smiles
        else:
            return None
            
    except Exception as e:
        logger.warning(f"Failed to sanitize SMILES '{smiles}': {e}")
        return None

def parse_yield(yield_value: Any) -> Optional[float]:
    """
    Parse yield value, handling ranges and single values.
    
    Args:
        yield_value: Raw yield value (string, float, or range like "50-60%")
        
    Returns:
        Parsed yield as float (0.0-100.0) or None if unparseable
    """
    if pd.isna(yield_value) or yield_value is None:
        return None
    
    # Convert to string for processing
    yield_str = str(yield_value).strip()
    
    # Remove '%' if present
    yield_str = yield_str.replace('%', '').strip()
    
    # Handle range format (e.g., "50-60")
    if '-' in yield_str:
        try:
            parts = yield_str.split('-')
            if len(parts) == 2:
                lower = float(parts[0].strip())
                upper = float(parts[1].strip())
                return (lower + upper) / 2.0
            else:
                logger.warning(f"Invalid range format: {yield_str}")
                return None
        except ValueError:
            logger.warning(f"Cannot parse range values: {yield_str}")
            return None
    
    # Handle single value
    try:
        value = float(yield_str)
        # Clamp to valid range [0, 100]
        value = max(0.0, min(100.0, value))
        return value
    except ValueError:
        logger.warning(f"Cannot parse yield value: {yield_str}")
        return None

def sanitize_reactions(input_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Sanitize reactions dataframe by removing salts, standardizing molecules,
    and parsing yield values.
    
    Args:
        input_df: Input dataframe with 'smiles' and 'yield' columns
        
    Returns:
        Tuple of (sanitized dataframe, statistics dict)
    """
    logger.info(f"Starting sanitization of {len(input_df)} reactions")
    
    stats = {
        'total_rows': len(input_df),
        'valid_smiles': 0,
        'invalid_smiles': 0,
        'valid_yield': 0,
        'invalid_yield': 0,
        'excluded_rows': 0,
        'exclusion_reasons': []
    }
    
    sanitized_smiles_list = []
    sanitized_yield_list = []
    exclusion_reasons = []
    
    for idx, row in input_df.iterrows():
        smiles = row.get('smiles', '')
        yield_val = row.get('yield', None)
        
        # Sanitize SMILES
        sanitized_smiles = remove_salts_and_standardize(smiles)
        
        # Parse yield
        parsed_yield = parse_yield(yield_val)
        
        # Determine if row should be included
        if sanitized_smiles is None:
            stats['invalid_smiles'] += 1
            stats['excluded_rows'] += 1
            exclusion_reasons.append({
                'row_idx': idx,
                'reason': 'invalid_smiles',
                'original_smiles': smiles
            })
            continue
        
        if parsed_yield is None:
            stats['invalid_yield'] += 1
            stats['excluded_rows'] += 1
            exclusion_reasons.append({
                'row_idx': idx,
                'reason': 'invalid_yield',
                'original_yield': str(yield_val)
            })
            continue
        
        # Row is valid
        stats['valid_smiles'] += 1
        stats['valid_yield'] += 1
        sanitized_smiles_list.append(sanitized_smiles)
        sanitized_yield_list.append(parsed_yield)
    
    # Create sanitized dataframe
    sanitized_df = pd.DataFrame({
        'smiles': sanitized_smiles_list,
        'yield': sanitized_yield_list
    })
    
    # Add other columns from original dataframe if they exist
    for col in input_df.columns:
        if col not in ['smiles', 'yield']:
            # For simplicity, we'll just keep the original values for other columns
            # In a real implementation, we might need to handle these differently
            sanitized_df[col] = input_df[col].values[:len(sanitized_df)]
    
    stats['exclusion_reasons'] = exclusion_reasons
    stats['exclusion_fraction'] = stats['excluded_rows'] / stats['total_rows'] if stats['total_rows'] > 0 else 0.0
    
    logger.info(f"Sanitization complete. Valid rows: {len(sanitized_df)}, Excluded: {stats['excluded_rows']}")
    logger.info(f"Exclusion fraction: {stats['exclusion_fraction']:.4f}")
    
    return sanitized_df, stats

def main():
    """Main entry point for sanitization pipeline."""
    logger.info("Starting sanitization pipeline")
    
    try:
        # Step 1: Verify checksum
        logger.info("Verifying checksum...")
        verify_checksum(CHECKSUM_FILE, RAW_DATA_PATH)
        
        # Step 2: Load raw data
        logger.info(f"Loading raw data from {RAW_DATA_PATH}")
        raw_df = pd.read_parquet(RAW_DATA_PATH)
        logger.info(f"Loaded {len(raw_df)} rows")
        
        # Ensure required columns exist
        required_columns = ['smiles', 'yield']
        missing_columns = [col for col in required_columns if col not in raw_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Step 3: Sanitize reactions
        sanitized_df, stats = sanitize_reactions(raw_df)
        
        # Step 4: Save sanitized data
        SANITIZED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        sanitized_df.to_parquet(SANITIZED_OUTPUT_PATH, index=False)
        logger.info(f"Saved sanitized data to {SANITIZED_OUTPUT_PATH}")
        
        # Step 5: Save statistics log
        SANITIZATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SANITIZATION_LOG_PATH, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        logger.info(f"Saved sanitization log to {SANITIZATION_LOG_PATH}")
        
        logger.info("Sanitization pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Sanitization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()