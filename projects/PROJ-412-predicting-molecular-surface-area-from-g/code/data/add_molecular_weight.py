import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir

logger = get_logger(__name__)

def calculate_molecular_weight(smiles: str) -> Optional[float]:
    """
    Calculate molecular weight from a SMILES string using RDKit.
    
    Args:
        smiles: SMILES string representing the molecule
        
    Returns:
        Molecular weight in g/mol, or None if parsing fails
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Descriptors.MolWt(mol)
    except Exception as e:
        logger.warning(f"Failed to calculate MW for SMILES '{smiles}': {e}")
        return None

def add_molecular_weight_column(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Load a parquet file containing molecule data, calculate molecular weight,
    and save the result with a new 'molecular_weight' column.
    
    Args:
        input_path: Path to input parquet file (created by T014)
        output_path: Path to output parquet file
        
    Returns:
        Dictionary with validation statistics
    """
    logger.info(f"Loading data from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load the parquet file
    df = pd.read_parquet(input_path)
    
    logger.info(f"Loaded {len(df)} molecules from {input_path}")
    
    # Verify required columns exist
    required_cols = ['smiles', 'node_features', 'edge_features']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Calculate molecular weight for each molecule
    logger.info("Calculating molecular weights...")
    molecular_weights = []
    null_count = 0
    
    for idx, row in df.iterrows():
        mw = calculate_molecular_weight(row['smiles'])
        if mw is None:
            null_count += 1
            molecular_weights.append(np.nan)
        else:
            molecular_weights.append(mw)
    
    df['molecular_weight'] = molecular_weights
    
    # Validation: Check for null values in molecular_weight
    mw_null_count = df['molecular_weight'].isna().sum()
    if mw_null_count > 0:
        logger.warning(f"Found {mw_null_count} molecules with null molecular weight")
    
    # Validation: Assert that 'charge' column exists in node_features and has no nulls
    charge_validation_passed = True
    charge_null_count = 0
    
    try:
        # Check if node_features is a list of dicts or a structured column
        first_node_features = df.iloc[0]['node_features']
        
        if isinstance(first_node_features, dict):
            # Single dict per row
            if 'charge' in first_node_features:
                if first_node_features['charge'] is None or (isinstance(first_node_features['charge'], float) and np.isnan(first_node_features['charge'])):
                    charge_validation_passed = False
                    charge_null_count = 1
                logger.info("node_features is a dict; checking 'charge' field")
            else:
                logger.warning("'charge' field not found in node_features dict")
                charge_validation_passed = False
        elif isinstance(first_node_features, list):
            # List of dicts (per atom)
            charge_found = False
            for item in first_node_features:
                if isinstance(item, dict) and 'charge' in item:
                    charge_found = True
                    if item['charge'] is None or (isinstance(item['charge'], float) and np.isnan(item['charge'])):
                        charge_validation_passed = False
                        charge_null_count += 1
            if not charge_found:
                logger.warning("'charge' field not found in any node_features dict")
                charge_validation_passed = False
        else:
            logger.warning(f"Unexpected node_features type: {type(first_node_features)}")
            charge_validation_passed = False
            
    except Exception as e:
        logger.error(f"Error validating charge column: {e}")
        charge_validation_passed = False
    
    # Save the output
    logger.info(f"Saving processed data to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    validation_stats = {
        "input_file": str(input_path),
        "output_file": str(output_path),
        "total_molecules": len(df),
        "mw_null_count": int(mw_null_count),
        "charge_validation_passed": charge_validation_passed,
        "charge_null_count": int(charge_null_count),
        "success": mw_null_count == 0 and charge_validation_passed
    }
    
    return validation_stats

def main():
    """Main entry point for T014b task."""
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    input_path = data_dir / "processed" / "graphs_with_features.parquet"
    output_path = data_dir / "processed" / "graphs_with_mw.parquet"
    validation_log_path = data_dir / "processed" / "validation_log.json"
    
    logger.info(f"Starting T014b: Calculate Molecular Weight")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        stats = add_molecular_weight_column(input_path, output_path)
        
        # Write validation log
        validation_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(validation_log_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Validation log written to {validation_log_path}")
        logger.info(f"Task completed successfully: {stats['success']}")
        
        if not stats['success']:
            logger.error("Validation failed. Check validation_log.json for details.")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Task failed: {e}")
        raise

if __name__ == "__main__":
    main()
