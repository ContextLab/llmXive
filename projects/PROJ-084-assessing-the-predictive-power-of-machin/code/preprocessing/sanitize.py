import logging
from typing import List, Optional
import pandas as pd
from rdkit import Chem
from rdkit.Chem import SanitizeMol, MolToSmiles, rdMolDescriptors
from pathlib import Path
import sys

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_RAW_DIR, DATA_PROCESSED_DIR
from utils.io import load_parquet, save_parquet

logger = logging.getLogger(__name__)

def remove_salts(smiles: str) -> Optional[str]:
    """Remove salts from a SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        # Simple heuristic: remove fragments with low molecular weight
        fragments = Chem.GetMolFrags(mol, asMols=True)
        if not fragments:
            return None
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
    original_count = len(df)
    logger.info(f"Starting sanitization on {original_count} rows.")

    # 1. Standardize SMILES
    logger.info("Standardizing SMILES...")
    df['canonical_smiles'] = df['smiles'].apply(standardize_smiles)
    dropped_std = df['canonical_smiles'].isna().sum()
    df = df.dropna(subset=['canonical_smiles'])
    logger.info(f"Standardization dropped {dropped_std} rows. Remaining: {len(df)}")

    # 2. Remove Salts
    logger.info("Removing salts...")
    df['cleaned_smiles'] = df['canonical_smiles'].apply(remove_salts)
    dropped_salts = df['cleaned_smiles'].isna().sum()
    df = df.dropna(subset=['cleaned_smiles'])
    logger.info(f"Salt removal dropped {dropped_salts} rows. Remaining: {len(df)}")

    # 3. Parse Yield
    logger.info("Parsing yields...")
    df['parsed_yield'] = df['yield'].apply(parse_yield)
    dropped_yield = df['parsed_yield'].isna().sum()
    df = df.dropna(subset=['parsed_yield'])
    logger.info(f"Yield parsing dropped {dropped_yield} rows. Remaining: {len(df)}")

    logger.info(f"Sanitization complete. Total dropped: {original_count - len(df)}")
    return df

def main():
    """
    Main entry point for T014.
    Loads USPTO parquet from data/raw/uspto_raw.parquet,
    sanitizes reactions, and saves to data/processed/cleaned_reactions.parquet.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    input_path = DATA_RAW_DIR / "uspto_raw.parquet"
    output_path = DATA_PROCESSED_DIR / "cleaned_reactions.parquet"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run T019 first.")
        raise FileNotFoundError(f"Input file {input_path} not found.")

    logger.info(f"Loading data from {input_path}...")
    df = load_parquet(input_path)

    if df.empty:
        logger.error("Loaded DataFrame is empty.")
        raise ValueError("Loaded DataFrame is empty.")

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    # Ensure required columns exist
    required_cols = ['smiles', 'yield']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info("Starting sanitization pipeline...")
    df_clean = sanitize_reactions(df)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving cleaned data to {output_path}...")
    save_parquet(df_clean, output_path)

    logger.info(f"Task T014 complete. Output saved to {output_path}")
    return df_clean

if __name__ == "__main__":
    main()