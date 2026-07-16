import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_steric_index(smiles: str) -> float:
    """
    Calculate steric index based on rotatable bonds and Crippen descriptors.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 999.0 # Invalid molecule
        
        rotatable = Descriptors.NumRotatableBonds(mol)
        # Crippen descriptors (LogP, MR) - using MR as a proxy for size/sterics
        # Note: CalcCrippenDescriptors returns (LogP, MR)
        crippen = Descriptors.Crippen.MR(mol)
        
        # Simple heuristic: steric_index = rotatable + (MR / 10)
        steric = rotatable + (crippen / 10.0)
        return steric
    except Exception as e:
        logger.warning(f"Error calculating steric index for {smiles}: {e}")
        return 999.0

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """
    Canonicalize SMILES string.
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol)
    except Exception:
        return None

def is_primary_substrate(substrate_class: str) -> bool:
    """
    Check if substrate is primary.
    """
    return substrate_class.lower() == 'primary'

def clean_and_filter_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Clean SMILES and filter primary alkyl halides.
    """
    exclusions = []
    valid_rows = []
    
    for idx, row in df.iterrows():
        smiles = row['smiles']
        canonical = canonicalize_smiles(smiles)
        
        if canonical is None:
            exclusions.append({
                'row_index': idx,
                'reason': 'parsing_error',
                'original_smiles': smiles
            })
            continue
        
        # Filter primary
        if is_primary_substrate(row.get('substrate_class', '')):
            exclusions.append({
                'row_index': idx,
                'reason': 'invalid_substrate',
                'original_smiles': smiles
            })
            continue
        
        # Filter by steric index
        steric = calculate_steric_index(canonical)
        if steric > 2.0:
            # Depending on spec, this might be a filter or just a descriptor
            # T012 says: "Filter row if steric_index > 2.0"
            exclusions.append({
                'row_index': idx,
                'reason': 'invalid_substrate', # Using this as a catch-all for steric
                'original_smiles': smiles
            })
            continue
        
        valid_rows.append({
            'smiles': canonical,
            'rate_constant': row['rate_constant'],
            'substrate_class': row.get('substrate_class', 'tertiary')
        })
    
    return pd.DataFrame(valid_rows), exclusions

def main():
    parser = argparse.ArgumentParser(description="Clean and filter SN1 data")
    parser.add_argument("--input", type=str, default="data/raw/sn1_raw.csv")
    parser.add_argument("--output", type=str, default="data/processed/cleaned_sn1.csv")
    parser.add_argument("--exclusion-output", type=str, default="data/processed/exclusion_report_clean.csv")
    args = parser.parse_args()

    ensure_dirs()
    
    df = pd.read_csv(args.input)
    cleaned_df, exclusions = clean_and_filter_data(df)
    
    cleaned_df.to_csv(args.output, index=False)
    logger.info(f"Cleaned data saved to {args.output} ({len(cleaned_df)} rows)")
    
    if exclusions:
        pd.DataFrame(exclusions).to_csv(args.exclusion_output, index=False)
        logger.info(f"Exclusion report saved to {args.exclusion_output}")

if __name__ == "__main__":
    main()
