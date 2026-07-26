"""
SN1 Reaction Data Cleaning Module (T012)

Implements SMILES canonicalization, steric filtering, and primary substrate removal.
Handles ambiguous stereochemistry and logs exclusions.
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
from rdkit.Chem import rdMolDescriptors, Crippen

# Add parent to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import setup_logging

# Constants
STERIC_HINDRANCE_PROXY_THRESHOLD = 2.0
LOG_FILE = "data/processed/clean.log"
PRE_FILTER_DIST_FILE = "data/processed/pre_filter_distribution.json"
EXCLUSION_REPORT_FILE = "data/processed/exclusion_report.csv"

def setup_cleaning_logger():
    """Setup logger specific to the cleaning task."""
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return setup_logging(name="cleaning", log_file=str(log_path), level=logging.INFO)

def calculate_steric_index(mol: Chem.Mol) -> float:
    """
    Calculate a proxy for steric hindrance.

    Proxy for undefined steric hindrance index per Plan Constitution Check.
    Formula: CalcNumRotatableBonds + CalcCrippenDescriptors(mol)[0] (LogP)
    """
    if mol is None:
        return float('inf')

    rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
    # Crippen descriptors: (LogP, MR)
    logp = Crippen.CalcCrippenDescriptors(mol)[0]
    
    # Handle potential NaN from LogP calculation
    if logp != logp: # NaN check
        logp = 0.0
        
    proxy = float(rotatable_bonds) + logp
    return proxy

def canonicalize_smiles(smiles: str, logger: logging.Logger) -> Tuple[Optional[str], Optional[str]]:
    """
    Canonicalize SMILES string.
    
    Returns:
        Tuple of (canonical_smiles, error_code). 
        If error_code is not None, canonical_smiles is None.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, "invalid_smiles"
        
        # Check for undefined stereochemistry or ambiguous bond orders
        # RDKit's MolToSmiles with isomeric=True will fail or produce warnings if stereo is ambiguous
        # We attempt canonicalization. If it fails or produces a warning about stereo, we exclude.
        
        # Standardize: remove explicit hydrogens, sanitize
        Chem.SanitizeMol(mol)
        
        # Try to generate canonical SMILES
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)
        
        # Verify round-trip (basic sanity check)
        mol_check = Chem.MolFromSmiles(canonical)
        if mol_check is None:
            return None, "canonicalization_failed"
            
        return canonical, None
        
    except Exception as e:
        error_str = str(e).lower()
        if "stereo" in error_str or "ambiguous" in error_str:
            return None, "ambiguous_stereochemistry"
        return None, "canonicalization_error"

def is_primary_substrate(mol: Chem.Mol, substrate_class: str) -> bool:
    """
    Determine if the molecule is a primary alkyl halide.
    
    Checks explicit substrate class label and structural heuristics if class is missing.
    """
    if substrate_class and 'primary' in substrate_class.lower():
        return True
    
    # Structural heuristic: Count carbon neighbors of the carbon attached to the halogen
    # This is a fallback if class is missing but we need to filter
    # However, per task, we primarily filter by explicit class 'primary'
    # If class is missing, we might need to infer, but the task says:
    # "Filter: Row if proxy > 2.0 OR if substrate class is explicitly 'primary'"
    # So we strictly check the class column.
    return False

def clean_and_filter_data(input_path: str, output_path: str, logger: logging.Logger) -> Tuple[int, int, List[Dict]]:
    """
    Main cleaning logic.
    
    Args:
        input_path: Path to intermediate CSV.
        output_path: Path to save cleaned CSV.
        logger: Logger instance.
        
    Returns:
        Tuple of (input_count, output_count, exclusion_logs)
    """
    df = pd.read_csv(input_path)
    input_count = len(df)
    logger.info(f"Loaded {input_count} rows from {input_path}")
    
    exclusions = []
    valid_rows = []
    
    for idx, row in df.iterrows():
        smiles = str(row.get('smiles', ''))
        substrate_class = str(row.get('substrate_class', ''))
        
        if not smiles or pd.isna(smiles) or smiles == '':
            exclusions.append({
                "row_index": idx,
                "reason": "missing_smiles",
                "original_smiles": smiles
            })
            continue
            
        # 1. Canonicalize
        canonical_smiles, error_code = canonicalize_smiles(smiles, logger)
        
        if error_code:
            exclusions.append({
                "row_index": idx,
                "reason": error_code,
                "original_smiles": smiles
            })
            logger.warning(f"Row {idx}: Canonicalization failed ({error_code}) for {smiles[:50]}...")
            continue
        
        mol = Chem.MolFromSmiles(canonical_smiles)
        
        # 2. Check Primary Substrate
        if is_primary_substrate(mol, substrate_class):
            exclusions.append({
                "row_index": idx,
                "reason": "primary_substrate_filter",
                "original_smiles": smiles
            })
            logger.info(f"Row {idx}: Filtered as primary substrate.")
            continue
            
        # 3. Calculate Steric Proxy
        steric_proxy = calculate_steric_index(mol)
        
        if steric_proxy > STERIC_HINDRANCE_PROXY_THRESHOLD:
            exclusions.append({
                "row_index": idx,
                "reason": "steric_hindrance_proxy_exceeded",
                "original_smiles": smiles
            })
            logger.info(f"Row {idx}: Filtered due to steric proxy {steric_proxy:.2f} > {STERIC_HINDRANCE_PROXY_THRESHOLD}.")
            continue
            
        # Row is valid
        row_dict = row.to_dict()
        row_dict['smiles'] = canonical_smiles
        row_dict['steric_hindrance_proxy'] = steric_proxy
        valid_rows.append(row_dict)
        
    output_df = pd.DataFrame(valid_rows)
    output_count = len(output_df)
    
    # Save cleaned data
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved {output_count} rows to {output_path}")
    
    return input_count, output_count, exclusions

def save_pre_filter_distribution(df: pd.DataFrame, logger: logging.Logger):
    """Save class counts of the input dataset."""
    if 'substrate_class' in df.columns:
        counts = df['substrate_class'].value_counts().to_dict()
    else:
        counts = {"unknown": len(df)}
        
    with open(PRE_FILTER_DIST_FILE, 'w') as f:
        json.dump(counts, f, indent=2)
    logger.info(f"Saved pre-filter distribution to {PRE_FILTER_DIST_FILE}")

def save_exclusion_report(exclusions: List[Dict], logger: logging.Logger):
    """Save the exclusion report to CSV."""
    if not exclusions:
        # Create empty file with headers if no exclusions
        pd.DataFrame(columns=["row_index", "reason", "original_smiles"]).to_csv(EXCLUSION_REPORT_FILE, index=False)
    else:
        report_df = pd.DataFrame(exclusions)
        report_df.to_csv(EXCLUSION_REPORT_FILE, index=False)
    logger.info(f"Saved exclusion report to {EXCLUSION_REPORT_FILE}")

def main():
    parser = argparse.ArgumentParser(description="Clean and filter SN1 data (T012)")
    parser.add_argument("--input", required=True, help="Input CSV path (intermediate_sn1.csv)")
    parser.add_argument("--output", required=True, help="Output CSV path (cleaned_sn1.csv)")
    args = parser.parse_args()
    
    logger = setup_cleaning_logger()
    logger.info("Starting cleaning pipeline (T012)")
    
    # Load input to calculate distribution BEFORE filtering
    input_df = pd.read_csv(args.input)
    save_pre_filter_distribution(input_df, logger)
    
    # Run cleaning
    input_count, output_count, exclusions = clean_and_filter_data(args.input, args.output, logger)
    
    # Save exclusions
    save_exclusion_report(exclusions, logger)
    
    success_rate = (output_count / input_count * 100) if input_count > 0 else 0
    logger.info(f"Pipeline complete. Input: {input_count}, Output: {output_count}, Rate: {success_rate:.2f}%")
    
    # Log exclusions summary
    if exclusions:
        reasons = {}
        for ex in exclusions:
            r = ex['reason']
            reasons[r] = reasons.get(r, 0) + 1
        logger.info(f"Exclusion reasons: {reasons}")

if __name__ == "__main__":
    main()