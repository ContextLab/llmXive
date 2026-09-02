import logging
from typing import List, Optional, Tuple
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import rdMolDescriptors
from pathlib import Path
import sys
import os

# Add project root to path to ensure imports work when run as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_PROCESSED_DIR
from utils.io import load_parquet, save_parquet

logger = logging.getLogger(__name__)

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """Get the Murcko scaffold for a SMILES string.
    
    Args:
        smiles: Canonical SMILES string of a molecule.
        
    Returns:
        SMILES string of the Murcko scaffold, or None if parsing fails.
    """
    if not smiles or not isinstance(smiles, str):
        return None
        
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        scaffold = MurckoScaffold.GetScaffoldForMol(mol, makeChiral=False, minNonRingSize=0)
        if scaffold is None:
            return None
            
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.warning(f"Failed to generate scaffold for SMILES '{smiles}': {e}")
        return None

def generate_scaffold_groups(df: pd.DataFrame, smiles_col: str = "canonical_smiles") -> pd.DataFrame:
    """Generate scaffold groups for a DataFrame by adding Murcko scaffold keys.
    
    This function implements FR-004 and Constitution Principle VI by grouping
    reactions based on their core molecular scaffolds to prevent data leakage
    in model evaluation.
    
    Args:
        df: DataFrame containing reaction data with a SMILES column.
        smiles_col: Name of the column containing canonical SMILES strings.
        
    Returns:
        DataFrame with an added 'murcko_scaffold' column containing scaffold keys.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame with scaffold column.")
        df = df.copy()
        df['murcko_scaffold'] = None
        return df
        
    logger.info(f"Generating Murcko scaffolds for {len(df)} reactions from column '{smiles_col}'...")
    
    df = df.copy()
    
    # Apply scaffold generation
    df['murcko_scaffold'] = df[smiles_col].apply(get_murcko_scaffold)
    
    # Log statistics
    total = len(df)
    valid_scaffolds = df['murcko_scaffold'].notna().sum()
    invalid_count = total - valid_scaffolds
    
    logger.info(f"Scaffold generation complete: {valid_scaffolds}/{total} valid scaffolds generated.")
    if invalid_count > 0:
        logger.warning(f"{invalid_count} reactions failed scaffold generation and will have NULL scaffold keys.")
    
    # Log scaffold distribution
    scaffold_counts = df['murcko_scaffold'].value_counts()
    logger.info(f"Generated {len(scaffold_counts)} unique scaffold groups.")
    
    return df

def main():
    """Main entry point for the scaffold generation pipeline.
    
    Reads cleaned reactions from data/processed/cleaned_reactions.parquet,
    generates Murcko scaffold grouping keys, and saves the result to
    data/processed/scaffold_groups.parquet.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    input_path = DATA_PROCESSED_DIR / "cleaned_reactions.parquet"
    output_path = DATA_PROCESSED_DIR / "scaffold_groups.parquet"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T017 (ingest.py) has been run successfully to generate cleaned_reactions.parquet")
        sys.exit(1)
    
    logger.info(f"Loading cleaned reactions from {input_path}...")
    try:
        df = load_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} reactions.")
    
    # Verify expected columns exist
    required_cols = ['canonical_smiles', 'yield_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in input data: {missing_cols}")
        sys.exit(1)
    
    # Generate scaffold groups
    df_scaffolded = generate_scaffold_groups(df, smiles_col='canonical_smiles')
    
    # Save results
    logger.info(f"Saving scaffold groups to {output_path}...")
    try:
        save_parquet(df_scaffolded, output_path)
        logger.info(f"Successfully saved {len(df_scaffolded)} records with scaffold keys to {output_path}")
        
        # Log final statistics
        unique_scaffolds = df_scaffolded['murcko_scaffold'].nunique()
        logger.info(f"Final output contains {unique_scaffolds} unique Murcko scaffold groups.")
        
    except Exception as e:
        logger.error(f"Failed to save output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()