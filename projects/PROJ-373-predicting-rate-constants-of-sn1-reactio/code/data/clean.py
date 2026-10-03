"""
code/data/clean.py

Implements canonicalization of SMILES and filtering of primary alkyl halides
for the SN1 rate constant prediction pipeline.

Logic:
1. Validate column values (specifically 'substrate_class').
2. Filter rows where 'substrate_class' == 'primary' (retain secondary/tertiary).
3. Standardize SMILES. If fails, exclude with code 'ambiguous_stereochemistry'.
4. Log all exclusions to data/processed/exclusion_raw.log and data/processed/clean.log.
5. Output: data/processed/cleaned_intermediate.csv.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

# Import project utilities
from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# --- Configuration Constants ---
VALID_SUBSTRATE_CLASSES = ['secondary', 'tertiary']
EXCLUDED_SUBSTRATE_CLASS = 'primary'
INVALID_SUBSTRATE_REASON = 'invalid_substrate_label'
AMBIGUOUS_STEREO_REASON = 'ambiguous_stereochemistry'
MISSING_INPUT_REASON = 'input_missing'
MISSING_SUBSTRATE_CLASS_REASON = 'missing_substrate_class'

# --- Logger Setup ---

def setup_cleaning_logger(log_path: Path) -> logging.Logger:
    """Sets up the logger for the cleaning process."""
    ensure_dirs(log_path)
    logger = logging.getLogger('cleaning')
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    if not logger.handlers: # Check again after file handler logic
        logger.addHandler(ch)
    
    # Remove duplicates if any added previously
    logger.handlers = list(set(logger.handlers))
    
    return logger

def log_fatal_error(logger: logging.Logger, reason: str, status_file: Path, log_file: Path):
    """Logs a fatal error and writes 'ABORTED' to the pipeline status file."""
    logger.error(f"FATAL ERROR: {reason}")
    write_aborted_status(status_file)
    # Also log to the clean.log if it exists or create it
    if log_file.exists():
       # Append to existing log
       with open(log_file, 'a') as f:
           f.write(f"{pd.Timestamp.now()} - FATAL - {reason}\n")
    else:
       # Create new log
       with open(log_file, 'w') as f:
           f.write(f"{pd.Timestamp.now()} - FATAL - {reason}\n")
    sys.exit(1)

def write_aborted_status(status_file: Path):
    """Writes 'ABORTED' to the pipeline status file."""
    ensure_dirs(status_file)
    with open(status_file, 'w') as f:
        f.write('ABORTED')

def save_exclusion_report(exclusion_log_path: Path, row_index: int, reason: str, smiles: str):
    """Appends an exclusion record to the exclusion_raw.log file."""
    ensure_dirs(exclusion_log_path)
    header_exists = exclusion_log_path.exists() and exclusion_log_path.stat().st_size > 0
    
    with open(exclusion_log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not header_exists:
            writer.writerow(['row_index', 'reason', 'original_smiles'])
        writer.writerow([row_index, reason, smiles])

# --- Data Processing Logic ---

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """
    Standardizes SMILES.
    Returns canonical SMILES if successful, None if failure (e.
    ambiguous stereochemistry).
    """
    if not smiles or not isinstance(smiles, str):
        return None
    
    try:
        mol = Chem.SmilesParser(smiles)
        if mol is None:
            return None
        # Canonicalize
        canonical = Chem.CanonicalSmiles(mol)
        return canonical
    except Exception:
        # RDKit might throw or return None for bad input
        return None

def is_primary_substrate(row: pd.Series) -> bool:
    """Checks if the row represents a primary substrate."""
    # Note: We retain secondary/tertiary. We filter OUT primary.
    # But for logging, we identify primary rows to exclude.
    if 'substrate_class' not in row:
        return False # Not a primary check, but missing class is handled elsewhere
    
    val = str(row['substrate_class']).strip().lower()
    return val == EXCLUDED_SUBSTRATE_CLASS

def validate_substrate_class_column(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validates that 'substrate_class' column exists and contains only explicit values.
    Returns True if valid, False otherwise.
    """
    if 'substrate_class' not in df.columns:
        logger.error("Column 'substrate_class' missing.")
        return False

    # Check for non-explicit values (e.g., 'unknown', 'mixed')
    unique_vals = df['substrate_class'].unique()
    non_explicit = [v for v in unique_vals if str(v).strip().lower() not in VALID_SUBSTRATE_CLASSES + [EXCLUDED_SUBSTRATE_CLASS]]
    
    if non_explicit:
        logger.error(f"Found non-explicit substrate class values: {non_explicit}")
        return False
    
    return True

def clean_and_filter_data(input_path: Path, output_path: Path, exclusion_log_path: Path, clean_log_path: Path, status_file_path: Path):
    """
    Main cleaning logic:
    1. Check input file existence.
    2. Load data.
    3. Validate 'substrate_class' column.
    4. Filter out primary substrates.
    5. Canonicalize SMILES.
    6. Log exclusions.
    7. Save output.
    """
    logger = setup_cleaning_logger(clean_log_path)
    logger.info(f"Starting cleaning process for {input_path}")

    # Guard Clause: Input missing or empty
    if not input_path.exists():
        log_fatal_error(logger, MISSING_INPUT_REASON, status_file_path, clean_log_path)
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        log_fatal_error(logger, f"Failed to read input CSV: {e}", status_file_path, clean_log_path)

    if df.empty:
        log_fatal_error(logger, MISSING_INPUT_REASON, status_file_path, clean_log_path)

    # Guard Clause (FR-009): Missing or non-explicit substrate_class
    if not validate_substrate_class_column(df, logger):
        log_fatal_error(logger, MISSING_SUBSTRATE_CLASS_REASON, status_file_path, clean_log_path)

    # Count initial rows
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} rows.")

    # Filter: Exclude rows where substrate_class == 'primary'
    # We KEEP secondary and tertiary.
    mask_valid_class = df['substrate_class'].str.lower().isin(VALID_SUBSTRATE_CLASSES)
    df_filtered_class = df[mask_valid_class]
    
    primary_count = initial_count - len(df_filtered_class)
    logger.info(f"Filtered out {primary_count} rows with 'primary' substrate class.")

    # Log exclusions for primary substrates to exclusion_raw.log
    if primary_count > 0:
        # Get the rows that were filtered out
        df_excluded_primary = df[~mask_valid_class]
        for idx, row in df_excluded_primary.iterrows():
            # Note: idx here is the original index from the CSV if we didn't reset it.
            # We should use the original row index if possible, or the current index if it matches.
            # Assuming the CSV has a consistent index or we use the current position.
            # The task says "row_index". Let's assume it's the original index or the position.
            # Using the index from the dataframe (which might be 0..N if reset, or original if not).
            # To be safe, let's assume the input CSV has a 'row_index' column or we use the dataframe index.
            # If the input is just raw, we use the integer index.
            original_idx = row.name if hasattr(row, 'name') else idx
            save_exclusion_report(exclusion_log_path, original_idx, 'primary_substrate_filter', str(row.get('smiles', '')))

    # SMILES Canonicalization
    logger.info("Canonicalizing SMILES...")
    valid_smiles_rows = []
    invalid_smiles_indices = []

    for idx, row in df_filtered_class.iterrows():
        smiles = str(row.get('smiles', ''))
        canonical = canonicalize_smiles(smiles)
        
        if canonical:
            valid_smiles_rows.append(canonical)
        else:
            invalid_smiles_indices.append(idx)
            save_exclusion_report(exclusion_log_path, idx, AMBIGUOUS_STEREO_REASON, smiles)

    # Update the dataframe with canonical smiles
    # We need to align the valid smiles with the rows
    # Since we iterated in order, we can assign directly if we didn't drop rows yet.
    # But we filtered by class first.
    
    # Create a new dataframe or update existing
    df_final = df_filtered_class.copy()
    df_final['smiles'] = valid_smiles_rows
    
    # Drop rows with invalid SMILES (they were logged above)
    # We need to drop by index.
    # Note: invalid_smiles_indices contains indices from the iterrows of df_filtered_class
    # which corresponds to the index of df_filtered_class.
    df_final = df_final.drop(index=invalid_smiles_indices)

    final_count = len(df_final)
    logger.info(f"Final row count after SMILES canonicalization: {final_count}")
    logger.info(f"Excluded {len(invalid_smiles_indices)} rows due to ambiguous stereochemistry.")

    # CRITICAL: If zero valid rows, abort
    if final_count == 0:
        log_fatal_error(logger, "Zero valid rows remaining after filtering and canonicalization.", status_file_path, clean_log_path)

    # Ensure output directory exists
    ensure_dirs(output_path)

    # Save output
    df_final.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

    # Log summary to clean.log
    with open(clean_log_path, 'a') as f:
        f.write(f"Summary: Initial={initial_count}, FilteredPrimary={primary_count}, InvalidSMILES={len(invalid_smiles_indices)}, Final={final_count}\n")

# --- Main Entry Point ---

def main():
    parser = argparse.ArgumentParser(description="Clean and filter SN1 data.")
    parser.add_argument('--input', type=str, required=True, help='Input CSV path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV path')
    parser.add_argument('--exclusion-log', type=str, required=True, help='Path to exclusion log')
    parser.add_argument('--clean-log', type=str, default='data/processed/clean.log', help='Path to clean log')
    
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    exclusion_log_path = Path(args.exclusion_log)
    clean_log_path = Path(args.clean_log)
    status_file_path = Path('data/processed/.pipeline_status')

    # Check pipeline status before running
    if status_file_path.exists():
        with open(status_file_path, 'r') as f:
            status = f.read().strip()
            if status == 'ABORTED':
                print("Pipeline status is ABORTED. Exiting.")
                sys.exit(1)

    clean_and_filter_data(input_path, output_path, exclusion_log_path, clean_log_path, status_file_path)

if __name__ == '__main__':
    main()
