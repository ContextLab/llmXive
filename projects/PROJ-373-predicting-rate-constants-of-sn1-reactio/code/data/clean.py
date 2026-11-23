"""
code/data/clean.py
Implements T012: Canonicalize SMILES and filter primary alkyl halides.
"""
import os
import sys
import json
import logging
import argparse
import csv
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

# Import shared utilities
# Note: ensure_dirs is defined in code/config.py and must accept *args/kwargs as per contract
try:
    from config import ensure_dirs, DataConfig
except ImportError:
    # Fallback for execution context where relative import might differ
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config import ensure_dirs, DataConfig

# Logger setup
logger = logging.getLogger(__name__)

# Constants
VALID_SUBSTRATE_CLASSES = ['secondary', 'tertiary']
PRIMARY_SUBSTRATE_LABEL = 'primary'
EXCLUSION_LOG_HEADER = ['row_index', 'reason', 'original_smiles']

def setup_cleaning_logger(log_path: Path) -> logging.Logger:
    """
    Sets up a logger for the cleaning process.
    """
    ensure_dirs(log_path.parent)
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    return root_logger

def log_fatal_error(log_path: Path, status: str, reason: str, message: str):
    """
    Logs a fatal error to the clean.log file.
    """
    ensure_dirs(log_path.parent)
    with open(log_path, 'a') as f:
        f.write(f"{status}|{reason}|{message}\n")
    logger.error(f"FATAL: {reason} - {message}")

def write_aborted_status(status_path: Path):
    """
    Writes 'ABORTED' to the pipeline status file.
    """
    ensure_dirs(status_path.parent)
    with open(status_path, 'w') as f:
        f.write('ABORTED')
    logger.critical("Pipeline status set to ABORTED.")

def save_exclusion_report(exclusion_log_path: Path, row_index: int, reason: str, smiles: str):
    """
    Appends an exclusion entry to the exclusion log.
    """
    ensure_dirs(exclusion_log_path.parent)
    file_exists = exclusion_log_path.exists()
    
    with open(exclusion_log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(EXCLUSION_LOG_HEADER)
        writer.writerow([row_index, reason, smiles])

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """
    Attempts to canonicalize a SMILES string using RDKit.
    Returns None if the SMILES is invalid or ambiguous.
    """
    if not smiles or not isinstance(smiles, str):
        return None
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Check for stereochemistry ambiguity
        # RDKit's MolToSmiles canonicalizes but we check for explicit stereo warnings if needed
        # For this task, if MolFromSmiles succeeds, we consider it valid structure.
        # If we need strict stereo handling, we can use Chem.MolToSmiles with isomeric=True
        
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        return canonical
    except Exception:
        return None

def is_primary_substrate(substrate_class: str) -> bool:
    """
    Checks if the substrate class indicates a primary alkyl halide.
    """
    return substrate_class and substrate_class.lower() == PRIMARY_SUBSTRATE_LABEL

def validate_substrate_class_column(df: pd.DataFrame, log_path: Path, status_path: Path) -> bool:
    """
    Validates that the 'substrate_class' column exists and contains only valid explicit values.
    Returns False if the column is missing or contains non-explicit values (e.g., 'unknown').
    """
    if 'substrate_class' not in df.columns:
        log_fatal_error(log_path, 'fatal_error', 'missing_substrate_class', 
                      "Column 'substrate_class' not found in input dataframe.")
        write_aborted_status(status_path)
        return False
    
    # Check for non-explicit values
    unique_values = df['substrate_class'].unique()
    invalid_values = [v for v in unique_values if v not in VALID_SUBSTRATE_CLASSES and v != PRIMARY_SUBSTRATE_LABEL]
    
    if invalid_values:
        # Log specific invalid values found
        msg = f"Found invalid substrate class values: {invalid_values}. Only {VALID_SUBSTRATE_CLASSES + [PRIMARY_SUBSTRATE_LABEL]} allowed."
        log_fatal_error(log_path, 'fatal_error', 'missing_substrate_class', msg)
        write_aborted_status(status_path)
        return False
        
    return True

def clean_and_filter_data(input_path: Path, output_path: Path, exclusion_log_path: Path, clean_log_path: Path, status_path: Path) -> bool:
    """
    Main logic to clean SMILES, validate substrate class, and filter primary substrates.
    """
    # Guard Clause: Check input file
    if not input_path.exists():
        log_fatal_error(clean_log_path, 'fatal_error', 'input_missing', 
                      f"Input file not found: {input_path}")
        write_aborted_status(status_path)
        return False

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        log_fatal_error(clean_log_path, 'fatal_error', 'input_read_failed', 
                      f"Failed to read input CSV: {str(e)}")
        write_aborted_status(status_path)
        return False

    if df.empty:
        log_fatal_error(clean_log_path, 'fatal_error', 'input_empty', 
                      "Input dataframe is empty.")
        write_aborted_status(status_path)
        return False

    # Guard Clause: Validate substrate class column
    if not validate_substrate_class_column(df, clean_log_path, status_path):
        return False

    # Initialize exclusion list for this run (we append to file, but track for final check)
    exclusions_this_run = 0
    valid_rows = []

    logger.info(f"Processing {len(df)} rows...")

    for idx, row in df.iterrows():
        original_smiles = str(row.get('smiles', ''))
        substrate_class = str(row.get('substrate_class', ''))
        
        # 1. Validate Substrate Class Label
        if substrate_class not in VALID_SUBSTRATE_CLASSES:
            if substrate_class == PRIMARY_SUBSTRATE_LABEL:
                # Filter primary: log and skip
                save_exclusion_report(exclusion_log_path, idx, 'primary_substrate_filter', original_smiles)
                exclusions_this_run += 1
                continue
            else:
                # Invalid label (e.g., 'unknown' if it slipped through initial check, or mixed)
                save_exclusion_report(exclusion_log_path, idx, 'invalid_substrate_label', original_smiles)
                exclusions_this_run += 1
                continue

        # 2. Canonicalize SMILES
        canonical_smiles = canonicalize_smiles(original_smiles)
        if canonical_smiles is None:
            # Determine reason: ambiguous structure vs stereo
            # For simplicity in this task, we treat any failure as ambiguous_structure
            # unless we have specific stereo logic.
            reason = 'ambiguous_structure'
            save_exclusion_report(exclusion_log_path, idx, reason, original_smiles)
            exclusions_this_run += 1
            continue

        # Row is valid
        row_dict = row.to_dict()
        row_dict['smiles'] = canonical_smiles
        valid_rows.append(row_dict)

    # Create output dataframe
    if not valid_rows:
        log_fatal_error(clean_log_path, 'fatal_error', 'no_valid_rows', 
                      "Zero valid rows remaining after filtering. Pipeline aborted.")
        write_aborted_status(status_path)
        return False

    output_df = pd.DataFrame(valid_rows)
    
    # Ensure output directory exists
    ensure_dirs(output_path.parent)
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Cleaning complete. Output: {len(output_df)} rows. Excluded: {exclusions_this_run} rows.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Clean and filter SN1 dataset.")
    parser.add_argument('--input', required=True, help='Path to input intermediate CSV')
    parser.add_argument('--output', required=True, help='Path to output cleaned CSV')
    parser.add_argument('--exclusion-log', required=True, help='Path to exclusion log file')
    parser.add_argument('--clean-log', default='data/processed/clean.log', help='Path to clean log file')
    parser.add_argument('--status', default='data/processed/.pipeline_status', help='Path to pipeline status file')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    exclusion_log_path = Path(args.exclusion_log)
    clean_log_path = Path(args.clean_log)
    status_path = Path(args.status)
    
    # Setup logger
    setup_cleaning_logger(clean_log_path)
    
    logger.info("Starting clean and filter process.")
    
    success = clean_and_filter_data(input_path, output_path, exclusion_log_path, clean_log_path, status_path)
    
    if not success:
        sys.exit(1)
        
    logger.info("Process completed successfully.")
    sys.exit(0)

if __name__ == '__main__':
    main()