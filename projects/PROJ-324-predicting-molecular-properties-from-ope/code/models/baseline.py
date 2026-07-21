"""
Baseline model module using Crippen's atomic contribution method.

This module computes additive fragment model predictions for molecular properties.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen

# Configure logging
logger = logging.getLogger(__name__)

def compute_crippen_contributions(smiles: str) -> Dict[str, float]:
    """
    Compute Crippen's atomic contributions for a molecule.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Dictionary with logP, MR (molar refractivity), and other contributions.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {'logP': np.nan, 'MR': np.nan}

    # Crippen's method
    logP = Crippen.MolLogP(mol)
    MR = Crippen.MolMR(mol)

    return {'logP': logP, 'MR': MR}

def process_dataset(df: pd.DataFrame, property_column: str = 'logP') -> pd.DataFrame:
    """
    Process a dataset and compute Crippen predictions.

    Args:
        df: Input DataFrame with SMILES column.
        property_column: Target property column name.

    Returns:
        DataFrame with predictions added.
    """
    predictions = []
    for idx, row in df.iterrows():
        smiles = row['smiles']
        contribs = compute_crippen_contributions(smiles)
        predictions.append(contribs)

    pred_df = pd.DataFrame(predictions)
    result_df = pd.concat([df.reset_index(drop=True), pred_df], axis=1)
    return result_df

def save_predictions(df: pd.DataFrame, output_path: str) -> None:
    """
    Save predictions to disk.

    Args:
        df: DataFrame with predictions.
        output_path: Path to save the CSV file.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")

def main() -> None:
    """
    Main entry point for the baseline model pipeline.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    test_path = project_root / 'data' / 'derived' / 'test_set.csv'
    output_dir = project_root / 'data' / 'derived'

    if not test_path.exists():
        logger.error(f"Test set not found: {test_path}")
        sys.exit(1)

    # Load test set
    logger.info("Loading test set...")
    df_test = pd.read_csv(test_path)

    # Compute Crippen predictions
    logger.info("Computing Crippen predictions...")
    df_pred = process_dataset(df_test, property_column='logP')

    # Save predictions
    save_predictions(df_pred, str(output_dir / 'baseline_predictions.csv'))

    logger.info("Baseline predictions complete")

if __name__ == "__main__":
    main()
