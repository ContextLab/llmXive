"""
Sanitize reactions:
1. Remove salts
2. Standardize SMILES
3. Parse yield (handle ranges vs single values)

Returns (df_clean, exclusion_log) to support T018 data quality reporting.
"""
import logging
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
from rdkit import Chem
from rdkit.Chem import SanitizeMol, MolToSmiles, rdMolDescriptors
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def remove_salts(smiles: str) -> Optional[str]:
    """Remove salts from a reaction SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Get fragments
        fragments = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
        
        # Filter out small fragments (salts)
        # Heuristic: keep fragments with > 1 atom
        clean_frags = [f for f in fragments if f.GetNumAtoms() > 1]
        
        if not clean_frags:
            return None
        
        # Reconstruct
        clean_mol = Chem.CombineMols(clean_frags[0], clean_frags[1]) if len(clean_frags) > 1 else clean_frags[0]
        for frag in clean_frags[2:]:
            clean_mol = Chem.CombineMols(clean_mol, frag)
        
        return MolToSmiles(clean_mol)
    except Exception:
        return None

def standardize_smiles(smiles: str) -> Optional[str]:
    """Standardize SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Sanitize
        Chem.SanitizeMol(mol)
        
        # Canonicalize
        return MolToSmiles(mol, canonical=True)
    except Exception:
        return None

def parse_yield(yield_val) -> Optional[float]:
    """Parse yield value, handling ranges and malformed entries."""
    if pd.isna(yield_val) or yield_val is None:
        return None
    
    try:
        # Handle string ranges like "50-60"
        if isinstance(yield_val, str):
            if '-' in yield_val:
                parts = yield_val.split('-')
                # Take the average or the lower bound? Let's take the lower bound for safety
                return float(parts[0].strip())
            else:
                return float(yield_val)
        elif isinstance(yield_val, (int, float)):
            return float(yield_val)
        else:
            return None
    except (ValueError, TypeError):
        return None

def sanitize_reactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Sanitize the entire dataframe.
    Returns (cleaned_df, exclusion_log).
    """
    exclusion_log: Dict[str, int] = {
        "salt_removal_failed": 0,
        "smiles_standardization_failed": 0,
        "yield_parsing_failed": 0,
        "null_smiles": 0,
        "null_yield": 0
    }
    
    clean_rows = []
    
    for idx, row in df.iterrows():
        smiles = row.get('smiles')
        yield_val = row.get('yield')
        
        # Check for null SMILES
        if pd.isna(smiles):
            exclusion_log["null_smiles"] += 1
            continue
        
        # Remove salts
        clean_smiles = remove_salts(str(smiles))
        if clean_smiles is None:
            exclusion_log["salt_removal_failed"] += 1
            continue
        
        # Standardize SMILES
        std_smiles = standardize_smiles(clean_smiles)
        if std_smiles is None:
            exclusion_log["smiles_standardization_failed"] += 1
            continue
        
        # Parse yield
        parsed_yield = parse_yield(yield_val)
        if parsed_yield is None:
            exclusion_log["yield_parsing_failed"] += 1
            continue
        
        # Ensure yield is within valid range
        if parsed_yield < 0 or parsed_yield > 100:
            exclusion_log["yield_parsing_failed"] += 1
            continue
        
        # Create new row
        new_row = row.copy()
        new_row['smiles'] = std_smiles
        new_row['yield'] = parsed_yield
        clean_rows.append(new_row)
    
    if not clean_rows:
        return pd.DataFrame(), exclusion_log
    
    df_clean = pd.DataFrame(clean_rows)
    return df_clean, exclusion_log

def main():
    """Entry point for testing."""
    # Example usage
    logger.info("Sanitization module loaded.")

if __name__ == "__main__":
    main()
