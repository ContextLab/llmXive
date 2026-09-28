"""
T012: Implement code/data/clean.py to canonicalize SMILES and filter primary alkyl halides.

Input: data/processed/intermediate_sn1.csv (output of T011e).
Output: data/processed/cleaned_intermediate.csv.

Logic:
1. Validate column values.
2. If column exists and is explicit, filter rows where substrate_class == 'primary'.
3. Log all exclusions to data/processed/clean.log, explicitly recording the count of filtered primary rows.
4. Validate that substrate_class values are strictly in ['secondary', 'tertiary'].
5. Exclude and log any row with values other than these (e.g., 'unknown', 'mixed') to data/processed/exclusion_raw.log with reason 'invalid_substrate_label'.
6. Standardize SMILES. If fails, exclude with code 'ambiguous_stereochemistry'.
7. If the count of valid rows is zero, write 'ABORTED' to data/processed/.pipeline_status and exit.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import rdkit
from rdkit import Chem
from rdkit.Chem import CanonicalSmiles
from rdkit import RDLogger

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Import the exclusion log functions from T013 (or shared utilities)
# Note: Since T013 is not yet implemented, we will implement the logging logic here
# to ensure the exclusion_raw.log is updated correctly as per the task requirements.
# The task T013 will later append to this same file.
from data.init_exclusion_log import initialize_exclusion_log

# Constants
VALID_SUBSTRATE_CLASSES = {'secondary', 'tertiary'}
EXCLUSION_LOG_PATH = Path("data/processed/exclusion_raw.log")
CLEAN_LOG_PATH = Path("data/processed/clean.log")
PIPELINE_STATUS_PATH = Path("data/processed/.pipeline_status")
INPUT_FILE_PATH = Path("data/processed/intermediate_sn1.csv")
OUTPUT_FILE_PATH = Path("data/processed/cleaned_intermediate.csv")
INTERMEDIATE_LOG_PATH = Path("data/processed/clean.log")

def setup_cleaning_logger() -> logging.Logger:
    """Setup logging for the cleaning task."""
    return get_logger("cleaning", log_file=str(CLEAN_LOG_PATH))

def canonicalize_smiles(smiles: str) -> Tuple[Optional[str], bool]:
    """
    Canonicalize SMILES string.
    Returns (canonical_smiles, success).
    If canonicalization fails, returns (None, False).
    """
    try:
        mol = Chem.SmilesParser().parse(smiles)
        if mol is None:
            return None, False
        canonical = Chem.Smiles(mol)
        if canonical is None:
            return None, False
        return canonical, True
    except Exception:
        return None, False

def is_primary_substrate(substrate_class: str) -> bool:
    """Check if the substrate class is 'primary'."""
    return substrate_class == 'primary'

def log_fatal_error(logger: logging.Logger, reason: str, pipeline_status_path: Path):
    """Log a fatal error and write 'ABORTED' to the pipeline status file."""
    logger.error(f"FATAL ERROR: {reason}")
    try:
        with open(pipeline_status_path, 'w') as f:
            f.write('ABORTED')
    except Exception as e:
        logger.error(f"Failed to write ABORTED status to {pipeline_status_path}: {e}")
    sys.exit(1)

def write_aborted_status(logger: logging.Logger, pipeline_status_path: Path):
    """Write 'ABORTED' to the pipeline status file."""
    try:
        with open(pipeline_status_path, 'w') as f:
            f.write('ABORTED')
        logger.error("Pipeline status set to ABORTED.")
    except Exception as e:
        logger.error(f"Failed to write ABORTED status to {pipeline_status_path}: {e}")
    sys.exit(1)

def save_exclusion_report(exclusions: List[Dict[str, Any]], exclusion_log_path: Path, logger: logging.Logger):
    """Append exclusions to the exclusion_raw.log file."""
    # Ensure the header exists
    if not exclusion_log_path.exists():
        initialize_exclusion_log()

    # Append exclusions
    with open(exclusion_log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for exclusion in exclusions:
            writer.writerow([exclusion['row_index'], exclusion['reason'], exclusion['original_smiles']])
    logger.info(f"Saved {len(exclusions)} exclusions to {exclusion_log_path}")

def clean_and_filter_data(df: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Clean and filter the data.
    1. Validate substrate_class column.
    2. Filter out primary substrates.
    3. Exclude rows with invalid substrate labels.
    4. Canonicalize SMILES.
    5. Return cleaned dataframe and list of exclusions.
    """
    exclusions = []

    # Check if substrate_class column exists
    if 'substrate_class' not in df.columns:
        logger.error("Column 'substrate_class' not found in the input data.")
        return pd.DataFrame(), []

    # Validate substrate_class values
    invalid_labels = df[~df['substrate_class'].isin(VALID_SUBSTRATE_CLASSES)]
    if not invalid_labels.empty:
        logger.warning(f"Found {len(invalid_labels)} rows with invalid substrate labels.")
        for idx, row in invalid_labels.iterrows():
            exclusions.append({
                'row_index': idx,
                'reason': 'invalid_substrate_label',
                'original_smiles': row['smiles']
            })
        df = df[df['substrate_class'].isin(VALID_SUBSTRATE_CLASSES)]

    # Filter out primary substrates
    primary_mask = df['substrate_class'] == 'primary'
    if primary_mask.any():
        logger.info(f"Filtering out {primary_mask.sum()} primary substrate rows.")
        for idx in df[primary_mask].index:
            exclusions.append({
                'row_index': idx,
                'reason': 'primary_substrate_filter',
                'original_smiles': df.loc[idx, 'smiles']
            })
        df = df[~primary_mask]

    # Canonicalize SMILES
    canonicalized_smiles = []
    failed_smiles_indices = []
    for idx, row in df.iterrows():
        smiles = row['smiles']
        canonical, success = canonicalize_smiles(smiles)
        if success:
            canonicalized_smiles.append(canonical)
        else:
            failed_smiles_indices.append(idx)
            exclusions.append({
                'row_index': idx,
                'reason': 'ambiguous_stereochemistry',
                'original_smiles': smiles
            })

    if failed_smiles_indices:
        logger.warning(f"Failed to canonicalize {len(failed_smiles_indices)} SMILES strings.")
        df = df.drop(failed_smiles_indices)
        df['smiles'] = canonicalized_smiles

    return df, exclusions

def main():
    """Main function for T012: Clean and filter data."""
    logger = setup_cleaning_logger()
    ensure_dirs()

    # Guard Clause: Check if input file exists and is not empty
    if not INPUT_FILE_PATH.exists():
        log_fatal_error(logger, "input_missing", PIPELINE_STATUS_PATH)

    try:
        df = pd.read_csv(INPUT_FILE_PATH)
        if df.empty:
            log_fatal_error(logger, "input_empty", PIPELINE_STATUS_PATH)
    except Exception as e:
        log_fatal_error(logger, f"failed_to_read_input: {e}", PIPELINE_STATUS_PATH)

    # Clean and filter data
    cleaned_df, exclusions = clean_and_filter_data(df, logger)

    # Check if valid rows remain
    if cleaned_df.empty:
        write_aborted_status(logger, PIPELINE_STATUS_PATH)

    # Save cleaned data
    cleaned_df.to_csv(OUTPUT_FILE_PATH, index=False)
    logger.info(f"Saved cleaned data to {OUTPUT_FILE_PATH} with {len(cleaned_df)} rows.")

    # Save exclusions
    if exclusions:
        save_exclusion_report(exclusions, EXCLUSION_LOG_PATH, logger)
    else:
        logger.info("No exclusions to save.")

    # Log counts for SC-005 verification
    logger.info(f"Total rows processed: {len(df)}")
    logger.info(f"Rows excluded: {len(exclusions)}")
    logger.info(f"Rows remaining: {len(cleaned_df)}")

    # Write 'OK' to pipeline status
    try:
        with open(PIPELINE_STATUS_PATH, 'w') as f:
            f.write('OK')
        logger.info("Pipeline status set to OK.")
    except Exception as e:
        logger.error(f"Failed to write OK status to {PIPELINE_STATUS_PATH}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
