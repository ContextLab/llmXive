import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

def setup_cleaning_logger(log_path: Path) -> logging.Logger:
    """Set up a logger for the cleaning process."""
    logger = get_logger("cleaning", log_path)
    return logger

def calculate_steric_index(smiles: str) -> Optional[float]:
    """
    Calculate a simple steric index based on molecular weight and heavy atom count.
    This is a proxy for steric hindrance.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        mw = Descriptors.MolWt(mol)
        heavy_atoms = mol.GetNumHeavyAtoms()
        if heavy_atoms == 0:
            return None
        return mw / heavy_atoms
    except Exception:
        return None

def canonicalize_smiles(smiles: str) -> Tuple[Optional[str], str]:
    """
    Canonicalize a SMILES string.
    Returns (canonical_smiles, status) where status is 'success' or 'ambiguous_stereochemistry'.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, "invalid_smiles"
        
        # Try to sanitize and canonicalize
        Chem.SanitizeMol(mol)
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        
        # If we get here, standardization succeeded
        return canonical, "success"
    except Exception as e:
        # Check if it's a stereochemistry issue
        error_msg = str(e).lower()
        if "stereo" in error_msg or "chiral" in error_msg:
            return None, "ambiguous_stereochemistry"
        return None, "canonicalization_failed"

def is_primary_substrate(substrate_class: str) -> bool:
    """
    Check if the substrate class is explicitly 'primary'.
    Returns True if it is primary (to be filtered out), False otherwise.
    """
    if pd.isna(substrate_class):
        return False
    return str(substrate_class).strip().lower() == 'primary'

def clean_and_filter_data(
    input_path: Path,
    output_path: Path,
    log_path: Path,
    exclusion_log_path: Path
) -> None:
    """
    Main cleaning and filtering logic.
    1. Check if input file exists and is not empty.
    2. Check if 'substrate_class' column exists.
    3. Canonicalize SMILES.
    4. Filter out primary alkyl halides.
    5. Log all exclusions.
    """
    logger = setup_cleaning_logger(log_path)
    logger.info(f"Starting cleaning process for {input_path}")
    
    # Guard Clause: Check if input file exists and is not empty
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        log_fatal_error(log_path, "input_missing", "Input file does not exist")
        sys.exit(1)
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        log_fatal_error(log_path, "read_error", str(e))
        sys.exit(1)

    if df.empty:
        logger.error("Input file is empty")
        log_fatal_error(log_path, "input_empty", "Input file is empty")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Guard Clause: Check if 'substrate_class' column exists
    if 'substrate_class' not in df.columns:
        logger.error("Column 'substrate_class' not found in input data")
        log_fatal_error(log_path, "missing_column", "Column 'substrate_class' is missing")
        sys.exit(1)

    # Check for non-explicit values in substrate_class
    unique_classes = df['substrate_class'].unique()
    non_explicit = [c for c in unique_classes if pd.notna(c) and str(c).strip().lower() not in ['primary', 'secondary', 'tertiary']]
    if non_explicit:
        logger.warning(f"Found non-explicit substrate classes: {non_explicit}")
        # FR-009: Raise fatal error if column contains non-explicit values
        log_fatal_error(log_path, "non_explicit_labels", f"Found non-explicit substrate classes: {non_explicit}")
        sys.exit(1)

    # Initialize exclusion tracking
    exclusions = []
    primary_count = 0
    stereo_fail_count = 0
    invalid_smiles_count = 0

    # Process rows
    logger.info("Starting SMILES canonicalization and filtering...")
    
    # Filter out rows with missing SMILES first
    valid_smiles_df = df[df['smiles'].notna() & (df['smiles'] != '')]
    invalid_rows = df[df['smiles'].isna() | (df['smiles'] == '')]
    for _, row in invalid_rows.iterrows():
        exclusions.append({
            'row_index': row.name,
            'reason': 'missing_smiles',
            'original_smiles': row.get('smiles', ''),
            'substrate_class': row.get('substrate_class', 'unknown')
        })
        invalid_smiles_count += 1

    # Canonicalize and filter primary
    cleaned_rows = []
    for idx, row in valid_smiles_df.iterrows():
        smiles = row['smiles']
        canonical, status = canonicalize_smiles(smiles)
        
        if status != 'success':
            exclusions.append({
                'row_index': idx,
                'reason': status,
                'original_smiles': smiles,
                'substrate_class': row['substrate_class']
            })
            if status == 'ambiguous_stereochemistry':
                stereo_fail_count += 1
            continue

        # Check if primary
        if is_primary_substrate(row['substrate_class']):
            exclusions.append({
                'row_index': idx,
                'reason': 'primary_substrate_filter',
                'original_smiles': smiles,
                'substrate_class': row['substrate_class']
            })
            primary_count += 1
            continue

        # Add to cleaned rows with canonical SMILES
        new_row = row.copy()
        new_row['smiles'] = canonical
        cleaned_rows.append(new_row)

    # Create cleaned dataframe
    if cleaned_rows:
        cleaned_df = pd.DataFrame(cleaned_rows)
        cleaned_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(cleaned_df)} cleaned rows to {output_path}")
    else:
        logger.warning("No rows passed filtering. Creating empty output file.")
        # Create empty file with correct columns
        if not valid_smiles_df.empty:
            cleaned_df = valid_smiles_df.head(0)
        else:
            cleaned_df = df.head(0)
        cleaned_df.to_csv(output_path, index=False)

    # Log exclusions
    if exclusions:
        exclusions_df = pd.DataFrame(exclusions)
        exclusions_df.to_csv(exclusion_log_path, index=False)
        logger.info(f"Logged {len(exclusions)} exclusions to {exclusion_log_path}")
    
    # Log summary
    logger.info(f"Cleaning Summary:")
    logger.info(f"  - Input rows: {len(df)}")
    logger.info(f"  - Primary substrates filtered: {primary_count}")
    logger.info(f"  - Stereochemistry failures: {stereo_fail_count}")
    logger.info(f"  - Invalid SMILES: {invalid_smiles_count}")
    logger.info(f"  - Output rows: {len(cleaned_rows) if cleaned_rows else 0}")

def log_fatal_error(log_path: Path, reason: str, message: str) -> None:
    """Log a fatal error and exit."""
    log_dir = log_path.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write(f"status: fatal_error\n")
        f.write(f"reason: {reason}\n")
        f.write(f"message: {message}\n")
    
    # Also print to stderr
    print(f"FATAL ERROR: {reason} - {message}", file=sys.stderr)

def save_exclusion_report(exclusion_log_path: Path, report_path: Path) -> None:
    """Save a summary report of exclusions."""
    if not exclusion_log_path.exists():
        return
    
    df = pd.read_csv(exclusion_log_path)
    summary = df.groupby('reason').size().reset_index(name='count')
    summary.to_csv(report_path, index=False)

def main():
    """Main entry point for the cleaning script."""
    parser = argparse.ArgumentParser(description="Clean and filter SN1 reaction data")
    parser.add_argument("--input", type=str, help="Input CSV path")
    parser.add_argument("--output", type=str, help="Output CSV path")
    parser.add_argument("--log", type=str, help="Log file path")
    parser.add_argument("--exclusion-log", type=str, help="Exclusion log path")
    
    args = parser.parse_args()
    
    # Use config if not provided
    config = DataConfig()
    input_path = Path(args.input) if args.input else config.intermediate_sn1_path
    output_path = Path(args.output) if args.output else config.cleaned_intermediate_path
    log_path = Path(args.log) if args.log else config.clean_log_path
    exclusion_log_path = Path(args.exclusion_log) if args.exclusion_log else config.exclusion_raw_log_path

    # Ensure directories exist
    ensure_dirs([output_path.parent, log_path.parent, exclusion_log_path.parent])

    # Run cleaning
    clean_and_filter_data(input_path, output_path, log_path, exclusion_log_path)

    # Generate exclusion report
    exclusion_report_path = config.exclusion_report_path
    save_exclusion_report(exclusion_log_path, exclusion_report_path)

    print(f"Cleaning completed successfully. Output: {output_path}")

if __name__ == "__main__":
    main()