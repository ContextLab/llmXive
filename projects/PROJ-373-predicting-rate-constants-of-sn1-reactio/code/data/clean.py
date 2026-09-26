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

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# --- Configuration & Constants ---
DATA_CONFIG = DataConfig()

# Output paths
INTERMEDIATE_PATH = DATA_CONFIG.intermediate_sn1_path
CLEANED_PATH = DATA_CONFIG.cleaned_intermediate_path
CLEAN_LOG_PATH = DATA_CONFIG.clean_log_path
PIPELINE_STATUS_PATH = DATA_CONFIG.pipeline_status_path

# Logging
logger = get_logger("clean", DATA_CONFIG.log_dir)

def setup_cleaning_logger() -> logging.Logger:
    """Initialize and return the cleaning logger."""
    return logger

def canonicalize_smiles(smiles_str: str) -> Optional[str]:
    """
    Canonicalize a SMILES string using RDKit.
    Returns the canonical SMILES if successful, None otherwise.
    """
    try:
        mol = Chem.MolFromSmiles(smiles_str)
        if mol is None:
            return None
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        return canonical
    except Exception:
        return None

def is_primary_substrate(substrate_class: Any) -> bool:
    """
    Check if the substrate class is explicitly 'primary'.
    Returns True if it is primary (to be filtered out), False otherwise.
    """
    if pd.isna(substrate_class):
        return False
    val = str(substrate_class).strip().lower()
    return val == 'primary'

def clean_and_filter_data(input_path: Path, output_path: Path, log_path: Path) -> int:
    """
    Main logic to canonicalize SMILES and filter primary alkyl halides.
    
    Returns:
        int: Number of rows successfully processed and kept.
    
    Raises:
        ValueError: If input is missing, empty, or substrate_class is missing/invalid.
    """
    # 1. Guard Clause: Check if input file exists and is not empty
    if not input_path.exists():
        log_fatal_error(log_path, "input_missing", f"Input file not found: {input_path}")
        write_aborted_status()
        raise ValueError(f"Input file missing: {input_path}")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        log_fatal_error(log_path, "input_read_error", f"Failed to read input CSV: {e}")
        write_aborted_status()
        raise ValueError(f"Failed to read input CSV: {e}")

    if df.empty:
        log_fatal_error(log_path, "input_empty", "Input dataframe is empty.")
        write_aborted_status()
        raise ValueError("Input dataframe is empty.")

    # 2. Guard Clause (FR-009): Check for 'substrate_class' column
    if 'substrate_class' not in df.columns:
        log_fatal_error(log_path, "missing_substrate_class", "Column 'substrate_class' is missing.")
        write_aborted_status()
        raise ValueError("Column 'substrate_class' is missing in the input data.")

    # Check for non-explicit values (e. 'unknown', 'nan', '')
    # We need to ensure we can explicitly filter 'primary'
    # If the column contains a high proportion of 'unknown' or similar, we might still proceed
    # but the task says: "If contains non-explicit values (e.g., 'unknown'), raise a fatal error"
    # Let's interpret this as: if there are rows where the class is NOT clearly 'primary', 'secondary', or 'tertiary',
    # and specifically if we see 'unknown', we abort.
    # However, the task says "If column exists and is explicit".
    # Let's check if the column has valid explicit labels.
    unique_values = df['substrate_class'].dropna().unique()
    valid_explicit_labels = {'primary', 'secondary', 'tertiary'}
    
    # If there are values that are NOT in the valid explicit set AND are not 'primary' (which we filter),
    # we need to be careful. The instruction says: "If ... contains non-explicit values (e.g., 'unknown'), raise a fatal error".
    # So if 'unknown' is present, we abort.
    invalid_labels = [val for val in unique_values if str(val).lower().strip() not in valid_explicit_labels and str(val).lower().strip() != 'unknown']
    
    if 'unknown' in [str(v).lower().strip() for v in unique_values]:
        log_fatal_error(log_path, "missing_substrate_class", "Column 'substrate_class' contains non-explicit value 'unknown'.")
        write_aborted_status()
        raise ValueError("Column 'substrate_class' contains non-explicit value 'unknown'.")

    # 3. Process: Canonicalize SMILES and Filter
    exclusion_count = 0
    excluded_rows = []
    kept_count = 0

    # Ensure log file exists and has header if we are appending
    if not log_path.exists():
        with open(log_path, 'w') as f:
            f.write("row_index,reason,original_smiles\n")
    else:
        # Check if header exists, if not add it (though we created it above)
        pass

    # Iterate and process
    # We need to track original index or row number for logging
    for idx, row in df.iterrows():
        original_smiles = row.get('smiles', '')
        substrate_class = row.get('substrate_class', '')
        
        # Check if primary (to be filtered)
        if is_primary_substrate(substrate_class):
            excluded_rows.append({
                'row_index': idx,
                'reason': 'primary_substrate_filter',
                'original_smiles': str(original_smiles)
            })
            exclusion_count += 1
            continue

        # Canonicalize SMILES
        canonical_smiles = canonicalize_smiles(str(original_smiles))
        if canonical_smiles is None:
            excluded_rows.append({
                'row_index': idx,
                'reason': 'ambiguous_stereochemistry',
                'original_smiles': str(original_smiles)
            })
            exclusion_count += 1
            continue

        # Update the row with canonical SMILES
        df.at[idx, 'smiles'] = canonical_smiles
        kept_count += 1

    # Log exclusions to clean.log
    if excluded_rows:
        with open(log_path, 'a') as f:
            for exc in excluded_rows:
                f.write(f"{exc['row_index']},{exc['reason']},{exc['original_smiles']}\n")
        logger.info(f"Logged {len(excluded_rows)} exclusions to {log_path}")
    else:
        logger.info("No exclusions logged.")

    # Filter the dataframe to remove primary substrates and rows with failed canonicalization
    # We already handled primary substrates. We need to drop rows where canonicalization failed.
    # The 'canonicalize_smiles' function returns None on failure. We need to filter those out.
    # But we already skipped them in the loop above? No, we need to actually drop them from the df.
    # Let's re-do the filtering logic properly.
    
    # Re-filter: Keep rows where substrate_class is NOT 'primary' AND canonicalization succeeded
    # We can do this by creating a mask
    mask = pd.Series([True] * len(df))
    
    for idx, row in df.iterrows():
        # Check primary
        if is_primary_substrate(row.get('substrate_class', '')):
            mask.loc[idx] = False
            continue
        
        # Check canonicalization
        if canonicalize_smiles(str(row.get('smiles', ''))) is None:
            mask.loc[idx] = False
            continue

    filtered_df = df[mask]
    
    # Save the cleaned dataframe
    ensure_dirs(output_path.parent)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(filtered_df)} rows to {output_path}")
    logger.info(f"Filtered out {exclusion_count} rows (primary or failed canonicalization).")
    
    return len(filtered_df)

def log_fatal_error(log_path: Path, reason: str, message: str):
    """Log a fatal error to the clean.log file."""
    ensure_dirs(log_path.parent)
    with open(log_path, 'a') as f:
        f.write(f"status: 'fatal_error'\n")
        f.write(f"reason: '{reason}'\n")
        f.write(f"message: '{message}'\n")
        f.write("-" * 40 + "\n")
    logger.error(f"FATAL ERROR: {reason} - {message}")

def write_aborted_status():
    """Write 'ABORTED' to the pipeline status file."""
    ensure_dirs(Path(PIPELINE_STATUS_PATH).parent)
    with open(PIPELINE_STATUS_PATH, 'w') as f:
        f.write('ABORTED')
    logger.warning("Pipeline status set to ABORTED.")

def save_exclusion_report(exclusions: List[Dict], output_path: Path):
    """Save the exclusion report to a CSV file."""
    if not exclusions:
        logger.info("No exclusions to save.")
        return
    
    ensure_dirs(output_path.parent)
    df_excl = pd.DataFrame(exclusions)
    df_excl.to_csv(output_path, index=False)
    logger.info(f"Saved exclusion report to {output_path}")

def main():
    """Main entry point for the cleaning script."""
    parser = argparse.ArgumentParser(description="Clean and filter SN1 data.")
    parser.add_argument("--input", type=str, default=str(INTERMEDIATE_PATH), help="Path to input CSV")
    parser.add_argument("--output", type=str, default=str(CLEANED_PATH), help="Path to output CSV")
    parser.add_argument("--log", type=str, default=str(CLEAN_LOG_PATH), help="Path to exclusion log")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    log_path = Path(args.log)

    try:
        clean_and_filter_data(input_path, output_path, log_path)
        logger.info("Cleaning completed successfully.")
    except ValueError as e:
        logger.error(f"Cleaning failed with fatal error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during cleaning: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()