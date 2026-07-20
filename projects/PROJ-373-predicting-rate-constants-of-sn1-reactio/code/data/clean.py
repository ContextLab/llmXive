import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure imports work relative to project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_steric_index(smiles: str) -> float:
    """
    Calculate steric hindrance proxy using RDKit descriptors.
    Formula: NumRotatableBonds + CalcCrippenDescriptors[0] (LogP)
    Returns a high value (999.0) if molecule is invalid.
    
    This proxy is defined by the project to replace the undefined 
    'steric hindrance index' in the spec Edge Cases.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import rdMolDescriptors, Crippen

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 999.0

        # Calculate number of rotatable bonds
        rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
        
        # Calculate Crippen descriptors (LogP, MR)
        # CalcCrippenDescriptors returns (LogP, MR)
        logp = Crippen.CalcCrippenDescriptors(mol)[0]

        # Composite proxy: both are dimensionless (count + logP)
        steric_hindrance_proxy = rotatable + logp
        return steric_hindrance_proxy
    except Exception as e:
        logger.warning(f"Error calculating steric index for {smiles}: {e}")
        return 999.0

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """
    Canonicalize SMILES string using RDKit.
    Returns None if parsing fails.
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol)
    except Exception as e:
        logger.warning(f"Failed to canonicalize SMILES '{smiles}': {e}")
        return None

def is_primary_substrate(substrate_class: Optional[str]) -> bool:
    """
    Check if substrate class is explicitly 'primary'.
    """
    if not substrate_class:
        return False
    return substrate_class.lower().strip() == 'primary'

def clean_and_filter_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Clean SMILES, canonicalize, and filter rows based on:
    1. Invalid SMILES (parsing error)
    2. Explicitly 'primary' substrate class
    3. Steric hindrance proxy > 2.0
    
    Filtering Rule from T012:
    - Calculate steric_hindrance_proxy = CalcNumRotatableBonds + CalcCrippenDescriptors[0] (LogP)
    - Filter row if steric_hindrance_proxy > 2.0 OR if substrate class is explicitly 'primary'
    
    Returns a tuple of (cleaned_dataframe, list_of_exclusion_dicts).
    """
    exclusions = []
    valid_rows = []

    for idx, row in df.iterrows():
        original_smiles = str(row['smiles'])
        substrate_class = row.get('substrate_class', '')

        # 1. Canonicalize SMILES
        canonical = canonicalize_smiles(original_smiles)
        if canonical is None:
            exclusions.append({
                'row_index': int(idx),
                'reason': 'canonicalization_error',
                'original_smiles': original_smiles
            })
            continue

        # 2. Filter primary substrates
        if is_primary_substrate(substrate_class):
            exclusions.append({
                'row_index': int(idx),
                'reason': 'primary_substrate',
                'original_smiles': original_smiles
            })
            continue

        # 3. Filter by steric hindrance proxy
        steric_proxy = calculate_steric_index(canonical)
        if steric_proxy > 2.0:
            exclusions.append({
                'row_index': int(idx),
                'reason': 'high_steric_hindrance',
                'original_smiles': original_smiles
            })
            continue

        # Row is valid
        valid_rows.append({
            'smiles': canonical,
            'rate_constant': row['rate_constant'],
            'substrate_class': substrate_class
        })

    cleaned_df = pd.DataFrame(valid_rows)
    return cleaned_df, exclusions

def main():
    parser = argparse.ArgumentParser(description="Clean and filter SN1 data for T012")
    parser.add_argument("--input", type=str, default="data/raw/sn1_raw.csv",
                        help="Path to raw input CSV")
    parser.add_argument("--output", type=str, default="data/processed/cleaned_sn1.csv",
                        help="Path to save cleaned CSV")
    parser.add_argument("--exclusion-output", type=str, default="data/processed/exclusion_report_clean.csv",
                        help="Path to save exclusion report CSV")
    args = parser.parse_args()

    ensure_dirs()

    logger.info(f"Loading data from {args.input}")
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} rows")

    cleaned_df, exclusions = clean_and_filter_data(df)

    logger.info(f"Cleaning complete. Kept {len(cleaned_df)} rows, excluded {len(exclusions)} rows.")

    # Save cleaned data
    cleaned_df.to_csv(args.output, index=False)
    logger.info(f"Cleaned data saved to {args.output}")

    # Save exclusion report if any exclusions occurred
    if exclusions:
        exclusions_df = pd.DataFrame(exclusions)
        exclusions_df.to_csv(args.exclusion_output, index=False)
        logger.info(f"Exclusion report saved to {args.exclusion_output}")
    else:
        logger.info("No exclusions to report.")

if __name__ == "__main__":
    import argparse
    main()