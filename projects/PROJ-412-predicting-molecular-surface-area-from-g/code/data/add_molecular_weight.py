import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import rdkit.Chem as Chem
from rdkit.Chem import Descriptors

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging import get_logger
from utils.config import get_data_dir

logger = get_logger(__name__)

def calculate_molecular_weight(smiles: str) -> Optional[float]:
    """
    Calculate the molecular weight from a SMILES string using RDKit.
    
    Args:
        smiles: SMILES string representing the molecule
        
    Returns:
        Molecular weight in g/mol, or None if SMILES is invalid
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Descriptors.MolWt(mol)
    except Exception as e:
        logger.warning(f"Failed to calculate MW for SMILES '{smiles}': {e}")
        return None

def add_molecular_weight_column(input_path: Path, output_path: Path) -> None:
    """
    Load a parquet file containing molecular data, calculate molecular weight
    for each entry, and save to a new parquet file.
    
    Args:
        input_path: Path to input parquet file (should contain 'smiles' column)
        output_path: Path to output parquet file (will include 'molecular_weight' column)
    """
    logger.info(f"Loading data from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    
    if 'smiles' not in df.columns:
        raise ValueError(f"Input file must contain 'smiles' column. Found: {df.columns.tolist()}")
    
    logger.info(f"Processing {len(df)} molecules to calculate molecular weight...")
    
    # Calculate molecular weight for each SMILES
    molecular_weights = []
    valid_count = 0
    failed_count = 0
    
    for i, smiles in enumerate(df['smiles']):
        mw = calculate_molecular_weight(smiles)
        if mw is not None:
            molecular_weights.append(mw)
            valid_count += 1
        else:
            molecular_weights.append(None)
            failed_count += 1
        
        if (i + 1) % 10000 == 0:
            logger.info(f"Processed {i + 1}/{len(df)} molecules")
    
    df['molecular_weight'] = molecular_weights
    
    # Log statistics
    valid_pct = (valid_count / len(df)) * 100
    failed_pct = (failed_count / len(df)) * 100
    
    logger.info(f"Molecular weight calculation complete:")
    logger.info(f"  - Valid: {valid_count} ({valid_pct:.2f}%)")
    logger.info(f"  - Failed: {failed_count} ({failed_pct:.2f}%)")
    
    if failed_pct > 10:
        logger.warning(f"High failure rate ({failed_pct:.2f}%) for molecular weight calculation!")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving result to {output_path}")
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully added molecular_weight column to {output_path}")

def main():
    """Main entry point for the molecular weight calculation script."""
    data_dir = get_data_dir()
    input_path = data_dir / "processed" / "graphs_with_features.parquet"
    output_path = data_dir / "processed" / "graphs_with_features.parquet"
    
    # For this task, we update the file in place or create a temp and move
    # To be safe with potential concurrent reads, we write to a temp file first
    temp_path = data_dir / "processed" / "graphs_with_features_temp.parquet"
    
    try:
        add_molecular_weight_column(input_path, temp_path)
        # Replace original with the new file
        temp_path.replace(input_path)
        logger.info(f"Updated {input_path} with molecular weight column")
    except Exception as e:
        logger.error(f"Failed to add molecular weight: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
