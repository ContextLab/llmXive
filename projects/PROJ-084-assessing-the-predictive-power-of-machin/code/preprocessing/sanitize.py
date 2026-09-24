"""
Sanitization pipeline for USPTO reaction data.

Implements:
1. SHA256 checksum verification against download_checksum.txt
2. Salt removal using RDKit MolStandardize
3. Hydrogen removal and SMILES standardization
4. Yield parsing (delegated to T015 logic if needed, but core sanitization here)
5. Output of sanitized reactions to data/processed/cleaned_reactions.parquet
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
from rdkit.Chem import rdMolStandardize
from rdkit.Chem.MolStandardize import rdMolStandardize as MolStandardize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/sanitize_pipeline.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Import shared utilities
from utils.io import calculate_sha256, load_parquet, save_parquet
from config import ensure_dirs

# Constants
RAW_DATA_PATH = Path("data/raw/uspto_raw.parquet")
CHECKSUM_PATH = Path("data/results/download_checksum.txt")
OUTPUT_PATH = Path("data/processed/cleaned_reactions.parquet")
QUALITY_REPORT_PATH = Path("data/results/data_quality_report.json")


def calculate_sha256_file(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    return calculate_sha256(file_path)


def verify_checksum(expected_checksum_path: Path, actual_file_path: Path) -> bool:
    """
    Verify SHA256 checksum of actual_file_path against expected checksum.
    
    Args:
        expected_checksum_path: Path to file containing expected checksum
        actual_file_path: Path to file to verify
        
    Returns:
        True if checksums match, False otherwise
        
    Raises:
        FileNotFoundError: If expected checksum file contains "FAILED" or doesn't exist
    """
    if not expected_checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {expected_checksum_path}")
    
    with open(expected_checksum_path, 'r') as f:
        expected_content = f.read().strip()
    
    # Check for explicit failure marker
    if "FAILED" in expected_content.upper():
        raise FileNotFoundError("Download failed, no data available")
    
    # Extract checksum (format: "sha256: <hash>" or just "<hash>")
    if "sha256:" in expected_content.lower():
        expected_hash = expected_content.split("sha256:")[-1].strip()
    else:
        expected_hash = expected_content
    
    actual_hash = calculate_sha256_file(actual_file_path)
    
    if actual_hash.lower() != expected_hash.lower():
        logger.error(f"Checksum mismatch!")
        logger.error(f"Expected: {expected_hash}")
        logger.error(f"Actual:   {actual_hash}")
        return False
    
    logger.info(f"Checksum verification successful: {actual_hash}")
    return True


def remove_salts_and_standardize(smiles: str) -> Optional[str]:
    """
    Remove salts and standardize a single SMILES string.
    
    Args:
        smiles: Input SMILES string
        
    Returns:
        Sanitized SMILES string or None if invalid
    """
    if not smiles or not isinstance(smiles, str):
        return None
    
    try:
        # Parse SMILES to molecule
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Remove salts using RDKit's MolStandardize
        # Cleaner removes salts and standardizes
        cleaner = MolStandardize.Cleaner()
        mol_clean = cleaner.clean(mol)
        
        # Remove explicit hydrogens
        mol_no_hs = Chem.RemoveHs(mol_clean)
        
        # Canonicalize SMILES
        sanitized_smiles = Chem.MolToSmiles(mol_no_hs, isomericSmiles=True)
        
        # Validate output
        if sanitized_smiles and len(sanitized_smiles) > 0:
            return sanitized_smiles
        return None
        
    except Exception as e:
        logger.warning(f"Failed to sanitize SMILES '{smiles[:50]}...': {e}")
        return None


def parse_yield_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse yield values, handling ranges and invalid formats.
    
    Note: Full yield parsing strategy is implemented in T015.
    This function provides basic parsing for the sanitize pipeline.
    Default strategy: exclude ranges (T015 will override if configured).
    
    Args:
        df: DataFrame with 'yield' column
        
    Returns:
        DataFrame with parsed yield values (float)
    """
    def parse_single_yield(val):
        if pd.isna(val):
            return None
        
        val_str = str(val).strip()
        
        # Handle range formats (e.g., "70-80", "70 - 80")
        if '-' in val_str and val_str.count('-') == 1:
            try:
                parts = val_str.split('-')
                if len(parts) == 2:
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    # Default strategy: exclude ranges (T015 will handle this)
                    return None  # Mark for exclusion
            except (ValueError, AttributeError):
                return None
        
        # Handle single values
        try:
            return float(val_str)
        except (ValueError, TypeError):
            return None
    
    df = df.copy()
    df['yield_parsed'] = df['yield'].apply(parse_single_yield)
    return df


def sanitize_reactions(input_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Sanitize a batch of reactions.
    
    Args:
        input_df: DataFrame with 'smiles' and 'yield' columns
        
    Returns:
        Tuple of (sanitized DataFrame, stats dict)
    """
    total_rows = len(input_df)
    logger.info(f"Processing {total_rows} rows...")
    
    # Parse yields
    df_parsed = parse_yield_batch(input_df)
    
    # Remove rows with invalid yields (ranges will be excluded)
    valid_yield_mask = df_parsed['yield_parsed'].notna()
    excluded_yield_count = (~valid_yield_mask).sum()
    df_valid_yield = df_parsed[valid_yield_mask].copy()
    
    # Sanitize SMILES
    sanitized_smiles = df_valid_yield['smiles'].apply(remove_salts_and_standardize)
    valid_smiles_mask = sanitized_smiles.notna()
    excluded_smiles_count = (~valid_smiles_mask).sum()
    
    df_sanitized = df_valid_yield[valid_smiles_mask].copy()
    df_sanitized['smiles'] = sanitized_smiles[valid_smiles_mask]
    df_sanitized['yield'] = df_sanitized['yield_parsed']
    df_sanitized = df_sanitized.drop(columns=['yield_parsed'])
    
    stats = {
        'total_rows': total_rows,
        'excluded_yield': int(excluded_yield_count),
        'excluded_smiles': int(excluded_smiles_count),
        'final_rows': len(df_sanitized),
        'exclusion_fraction': (excluded_yield_count + excluded_smiles_count) / total_rows if total_rows > 0 else 0
    }
    
    logger.info(f"Sanitization complete: {stats['final_rows']}/{total_rows} rows retained")
    return df_sanitized, stats


def run_sanitization_pipeline() -> Dict[str, Any]:
    """
    Run the full sanitization pipeline.
    
    1. Verify checksum
    2. Load raw data
    3. Sanitize reactions
    4. Save output
    5. Generate quality report
    
    Returns:
        Pipeline statistics
    """
    logger.info("=" * 60)
    logger.info("Starting Sanitization Pipeline (T014)")
    logger.info("=" * 60)
    
    # Step 1: Verify checksum
    logger.info("Step 1: Verifying SHA256 checksum...")
    try:
        if not verify_checksum(CHECKSUM_PATH, RAW_DATA_PATH):
            raise ValueError("Checksum verification failed")
    except FileNotFoundError as e:
        logger.error(f"Checksum verification failed: {e}")
        raise
    
    # Step 2: Load raw data
    logger.info("Step 2: Loading raw data...")
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}")
    
    df_raw = load_parquet(RAW_DATA_PATH)
    logger.info(f"Loaded {len(df_raw)} rows from {RAW_DATA_PATH}")
    
    # Ensure required columns exist
    required_cols = ['smiles', 'yield']
    missing_cols = [col for col in required_cols if col not in df_raw.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Step 3: Sanitize reactions
    logger.info("Step 3: Sanitizing reactions...")
    df_sanitized, stats = sanitize_reactions(df_raw)
    
    # Step 4: Save output
    logger.info("Step 4: Saving sanitized data...")
    ensure_dirs(OUTPUT_PATH)
    save_parquet(df_sanitized, OUTPUT_PATH)
    logger.info(f"Saved {len(df_sanitized)} rows to {OUTPUT_PATH}")
    
    # Step 5: Update/Generate quality report
    logger.info("Step 5: Generating quality report...")
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'pipeline': 'sanitization',
        'input_file': str(RAW_DATA_PATH),
        'output_file': str(OUTPUT_PATH),
        'checksum_verified': True,
        **stats
    }
    
    # Append to existing report if it exists
    if QUALITY_REPORT_PATH.exists():
        with open(QUALITY_REPORT_PATH, 'r') as f:
            existing_report = json.load(f)
        if 'sanitization' not in existing_report:
            existing_report['sanitization'] = report_data
        else:
            existing_report['sanitization'].update(report_data)
        with open(QUALITY_REPORT_PATH, 'w') as f:
            json.dump(existing_report, f, indent=2)
    else:
        with open(QUALITY_REPORT_PATH, 'w') as f:
            json.dump({'sanitization': report_data}, f, indent=2)
    
    logger.info("=" * 60)
    logger.info("Sanitization Pipeline Complete")
    logger.info(f"Final rows: {stats['final_rows']}")
    logger.info(f"Exclusion fraction: {stats['exclusion_fraction']:.4f}")
    logger.info("=" * 60)
    
    return stats


def main():
    """Main entry point for sanitization pipeline."""
    try:
        stats = run_sanitization_pipeline()
        logger.info("Pipeline completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())