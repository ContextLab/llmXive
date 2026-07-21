"""
Baseline model module using Crippen's atomic contribution method.

This module implements the additive fragment model (Crippen et al.) to predict
molecular properties (logP, solubility, boiling point) based on atomic contributions.
It processes the held-out test set and outputs predictions to a CSV file.
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

# Project root resolution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED_DIR = ROOT_DIR / "data" / "derived"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "derived"

# Ensure output directory exists
DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

# Configure logger
logger = logging.getLogger(__name__)

def compute_crippen_contributions(smiles: str) -> Dict[str, float]:
    """
    Compute Crippen's atomic contributions for a molecule.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Dictionary with keys:
            - 'logP': Predicted logP (Crippen's XLogP)
            - 'solubility': Predicted solubility (logS)
            - 'boiling_point': Predicted boiling point (NaN as Crippen doesn't provide it)
            - 'molecular_weight': Molecular weight
            - 'num_atoms': Number of atoms
            - 'is_valid': Boolean indicating if the molecule was valid
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {'logP': np.nan, 'MR': np.nan}

    # Crippen's method
    logP = Crippen.MolLogP(mol)
    MR = Crippen.MolMR(mol)

    # Crippen's logS (Solubility)
    try:
        log_s_val = Crippen.MolLogS(mol)
        solubility_val = log_s_val
    except Exception:
        solubility_val = float('nan')

    # Boiling point: Crippen's additive model does not directly provide BP.
    boiling_point_val = float('nan')

    mw = Chem.Descriptors.MolWt(mol)
    num_atoms = mol.GetNumAtoms()

    return {
        'logP': logp_val,
        'solubility': solubility_val,
        'boiling_point': boiling_point_val,
        'molecular_weight': mw,
        'num_atoms': num_atoms,
        'is_valid': True
    }


def process_dataset(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the held-out test set and compute Crippen contributions for all molecules.

    Args:
        input_path: Path to the test set CSV file. Defaults to data/derived/test_set.csv.

    Returns:
        DataFrame with predictions added.
    """
    if input_path is None:
        input_path = DATA_PROCESSED_DIR / "test_set.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T011.5 (Train/Test Split) has been executed to produce test_set.csv."
        )

    logger.info(f"Loading test set from {input_path}")
    df = pd.read_csv(input_path)

    # Validate required columns
    if 'smiles' not in df.columns:
        raise ValueError("Input dataset must contain a 'smiles' column.")

    logger.info(f"Processing {len(df)} molecules from test set...")
    results = []

    for idx, row in df.iterrows():
        if idx % 500 == 0:
            logger.info(f"Processed {idx}/{len(df)} molecules")

        smiles = row['smiles']
        contribs = compute_crippen_contributions(smiles)
        contribs['smiles'] = smiles
        
        # Preserve original experimental values if they exist
        for col in df.columns:
            if col not in contribs:
                contribs[col] = row[col]
        
        results.append(contribs)

    logger.info("Crippen contribution calculation complete.")
    return pd.DataFrame(results)

def save_predictions(df: pd.DataFrame, output_path: str) -> None:
    """
    Save predictions to disk.

    Args:
        df: DataFrame with predictions.
        output_path: Path to save the CSV file.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Saved baseline predictions to {output_path}")


def main() -> None:
    """Main entry point for the baseline prediction pipeline."""
    logger.info("Starting Crippen baseline prediction pipeline on test set.")

    try:
        # 1. Process dataset (load test set) and compute contributions
        df_predictions = process_dataset()

        # 2. Save results to the required output path
        save_predictions(df_predictions)

        logger.info("Baseline prediction pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
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
