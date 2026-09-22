import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_cleaning_logger():
    """Setup logging for cleaning process."""
    return get_logger(__name__)

def canonicalize_smiles(smiles: str):
    """Canonicalize SMILES string using RDKit.
    
    Returns:
        Tuple of (canonical_smiles, error_code) where error_code is None on success.
    """
    if not isinstance(smiles, str) or not smiles.strip():
        return None, "invalid_smiles"
    
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, "invalid_smiles"
        
        # Standardize stereochemistry handling
        # If stereochemistry is ambiguous, RDKit may fail to canonicalize properly
        # We catch this and flag it
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        
        # Verify the canonicalization didn't produce an empty string
        if not canonical:
            return None, "ambiguous_stereochemistry"
            
        return canonical, None
    except Exception as e:
        logger.warning(f"Failed to canonicalize SMILES: {smiles}, error: {e}")
        # Check if it's a stereochemistry issue
        error_msg = str(e).lower()
        if "stereo" in error_msg or "chiral" in error_msg:
            return None, "ambiguous_stereochemistry"
        return None, "canonicalization_error"

def is_primary_substrate(substrate_class: Optional[str]) -> bool:
    """Check if substrate is primary alkyl halide.
    
    Filtering Rule: Filter rows where substrate_class is explicitly labeled as 'primary'
    (i.e., retain secondary/tertiary).
    """
    if substrate_class is None:
        return False
    return str(substrate_class).lower().strip() == 'primary'

def clean_and_filter_data(input_path: str, output_path: str, exclusion_log_path: str):
    """Clean and filter data based on substrate class.
    
    Logic:
    1) Check if substrate_class column exists. If missing, raise fatal error.
    2) If column exists, filter rows where substrate_class == 'primary'.
    3) Canonicalize SMILES and handle stereochemistry errors.
    4) Log all exclusions to exclusion log.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
        exclusion_log_path: Path to exclusion log CSV
        
    Returns:
        Tuple of (rows_kept, rows_excluded)
    """
    import pandas as pd
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    if df.empty:
        raise ValueError("Input file is empty")
    
    # Check for substrate_class column - CRITICAL for FR-009
    if 'substrate_class' not in df.columns:
        raise ValueError("Missing substrate_class column in input data")
    
    # Filter out primary substrates based on explicit label only
    initial_count = len(df)
    
    # Create a copy to avoid SettingWithCopyWarning
    df = df.copy()
    
    # Canonicalize SMILES and track failures
    canonical_smiles_list = []
    exclusion_reasons = []
    rows_to_keep = []
    
    for idx, row in df.iterrows():
        smiles = row.get('smiles', '')
        substrate_class = row.get('substrate_class', '')
        
        # Check if primary substrate
        if is_primary_substrate(substrate_class):
            exclusion_reasons.append('Primary substrate')
            canonical_smiles_list.append(smiles)
            rows_to_keep.append(False)
            continue
        
        # Canonicalize SMILES
        canonical, error = canonicalize_smiles(smiles)
        
        if error:
            exclusion_reasons.append(error)
            canonical_smiles_list.append(smiles)
            rows_to_keep.append(False)
            continue
        
        # Update canonical SMILES
        df.at[idx, 'smiles'] = canonical
        exclusion_reasons.append(None)
        canonical_smiles_list.append(canonical)
        rows_to_keep.append(True)
    
    # Create exclusion log DataFrame
    exclusion_data = []
    for idx, row in df.iterrows():
        if not rows_to_keep[idx]:
            exclusion_data.append({
                'row_index': idx,
                'reason': exclusion_reasons[idx],
                'original_smiles': row['smiles']
            })
    
    # Append to exclusion log
    if exclusion_data:
        exclusion_df = pd.DataFrame(exclusion_data)
        file_exists = os.path.exists(exclusion_log_path)
        exclusion_df.to_csv(
            exclusion_log_path, 
            mode='a', 
            header=not file_exists, 
            index=False
        )
        logger.info(f"Appended {len(exclusion_data)} exclusions to {exclusion_log_path}")
    
    # Filter the dataframe
    filtered_df = df[rows_to_keep].reset_index(drop=True)
    
    final_count = len(filtered_df)
    excluded_count = initial_count - final_count
    
    logger.info(f"Filtered {excluded_count} rows (primary substrates and stereochemistry errors)")
    logger.info(f"Kept {final_count} rows")
    
    # Save cleaned data
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(filtered_df)} rows to {output_path}")
    
    return final_count, excluded_count

def log_fatal_error(log_path: str, reason: str):
    """Log a fatal error to the clean.log file and exit.
    
    Args:
        log_path: Path to the log file
        reason: Reason for the fatal error
    """
    error_log = {
        'status': 'fatal_error',
        'reason': reason,
        'timestamp': str(datetime.now())
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, 'w') as f:
        json.dump(error_log, f, indent=2)
    
    logger.error(f"Fatal error: {reason}")
    sys.exit(1)

def save_exclusion_report(exclusion_path: str, output_path: str):
    """Save exclusion report from the raw log to a formatted CSV.
    
    Args:
        exclusion_path: Path to the exclusion log (exclusion_raw.log)
        output_path: Path to save the exclusion report
    """
    import pandas as pd
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(exclusion_path):
        df = pd.read_csv(exclusion_path)
        df.to_csv(output_path, index=False)
        logger.info(f"Exclusion report saved to {output_path}")
    else:
        # Create empty report with correct schema
        pd.DataFrame(columns=['row_index', 'reason', 'original_smiles']).to_csv(
            output_path, index=False
        )
        logger.info(f"Empty exclusion report saved to {output_path}")

def main():
    """Main entry point for the cleaning script."""
    parser = argparse.ArgumentParser(description="Clean and filter SN1 data")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/intermediate_sn1.csv", 
        help="Input file path"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/cleaned_intermediate.csv", 
        help="Output file path"
    )
    parser.add_argument(
        "--exclusion-log", 
        type=str, 
        default="data/processed/exclusion_raw.log", 
        help="Exclusion log path"
    )
    parser.add_argument(
        "--exclusion-report", 
        type=str, 
        default="data/processed/exclusion_report.csv", 
        help="Exclusion report path"
    )
    parser.add_argument(
        "--log-file", 
        type=str, 
        default="data/processed/clean.log", 
        help="Log file path"
    )
    args = parser.parse_args()

    ensure_dirs()
    
    # Guard Clause: Check input file existence
    if not os.path.exists(args.input):
        log_fatal_error(args.log_file, 'input_missing')
    
    try:
        # Clean and filter
        clean_and_filter_data(args.input, args.output, args.exclusion_log)
        
        # Save exclusion report
        save_exclusion_report(args.exclusion_log, args.exclusion_report)
        
        logger.info("Cleaning completed successfully")
        
    except ValueError as e:
        # Handle missing substrate_class or other validation errors
        log_fatal_error(args.log_file, str(e))
    except Exception as e:
        log_fatal_error(args.log_file, str(e))

if __name__ == "__main__":
    main()