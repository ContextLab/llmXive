import logging
from typing import List, Optional
import pandas as pd
from rdkit import Chem
from rdkit.Chem import SanitizeMol, MolToSmiles, rdMolDescriptors

logger = logging.getLogger(__name__)

def remove_salts(smiles: str) -> Optional[str]:
    """Remove salts from a SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        # Simple heuristic: remove fragments with low molecular weight
        fragments = Chem.GetMolFrags(mol, asMols=True)
        main_frag = max(fragments, key=lambda m: m.GetNumAtoms())
        return MolToSmiles(main_frag)
    except Exception as e:
        logger.warning(f"Failed to remove salts from {smiles}: {e}")
        return None

def standardize_smiles(smiles: str) -> Optional[str]:
    """Standardize a SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        # RDKit sanitization
        Chem.SanitizeMol(mol)
        return MolToSmiles(mol, canonical=True)
    except Exception as e:
        logger.warning(f"Failed to standardize {smiles}: {e}")
        return None

def parse_yield(yield_val) -> Optional[float]:
    """Parse yield value, handling ranges."""
    if pd.isna(yield_val):
        return None
    if isinstance(yield_val, (int, float)):
        return float(yield_val)
    if isinstance(yield_val, str):
        # Handle "80-90" -> 85
        if "-" in yield_val:
            parts = yield_val.split("-")
            try:
                return (float(parts[0]) + float(parts[1])) / 2.0
            except ValueError:
                return None
        try:
            return float(yield_val)
        except ValueError:
            return None
    return None

def sanitize_reactions(df: pd.DataFrame) -> pd.DataFrame:
    """Apply sanitization steps to a DataFrame of reactions."""
    df = df.copy()
    
    # Standardize SMILES
    df['canonical_smiles'] = df['smiles'].apply(standardize_smiles)
    df = df.dropna(subset=['canonical_smiles'])
    
    # Parse yield
    df['parsed_yield'] = df['yield'].apply(parse_yield)
    df = df.dropna(subset=['parsed_yield'])
    
    return df

if __name__ == "__main__":
    # Example usage
    pass
