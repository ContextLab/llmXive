"""
Baseline prediction module using Crippen's atomic contributions.

This module implements the additive fragment model (Crippen et al.) to predict
molecular properties (logP, solubility, boiling point) based on atomic contributions.
It processes the preprocessed dataset and outputs predictions to a CSV file.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
from rdkit import Chem
from rdkit.Chem import Crippen

# Project root resolution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED_DIR = ROOT_DIR / "data" / "derived"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"

# Ensure output directory exists
DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def compute_crippen_contributions(smiles: str) -> Dict[str, float]:
    """
    Compute Crippen's atomic contributions for a single molecule.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Dictionary with keys:
            - 'logP': Predicted logP (Crippen's XLogP)
            - 'solubility': Predicted solubility (approximated via logS if available, else None)
            - 'boiling_point': Predicted boiling point (not directly in Crippen, returns NaN)
            - 'molecular_weight': Molecular weight
            - 'num_atoms': Number of atoms
            - 'is_valid': Boolean indicating if the molecule was valid
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {
            'logP': float('nan'),
            'solubility': float('nan'),
            'boiling_point': float('nan'),
            'molecular_weight': float('nan'),
            'num_atoms': 0,
            'is_valid': False
        }

    # Crippen's logP (XLogP)
    try:
        logp_val = Crippen.MolLogP(mol)
    except Exception:
        logp_val = float('nan')

    # Crippen's logS (Solubility) - Note: RDKit's Crippen module has MolLogS
    try:
        log_s_val = Crippen.MolLogS(mol)
        # Convert logS (mol/L) to solubility in mg/L approx?
        # Usually logS is log10(mol/L). Let's store logS directly as the metric.
        solubility_val = log_s_val
    except Exception:
        solubility_val = float('nan')

    # Boiling point: Crippen's additive model does not directly provide BP.
    # We will leave this as NaN for the baseline, as the task specifies
    # "Crippen's additive fragment model" which is primarily for LogP and LogS.
    # If a heuristic is strictly required, it would be outside standard Crippen.
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
    Load the preprocessed dataset and compute Crippen contributions for all molecules.

    Args:
        input_path: Path to the preprocessed CSV file. Defaults to data/processed/preprocessed_data.csv.

    Returns:
        DataFrame containing original data plus Crippen predictions.
    """
    if input_path is None:
        input_path = DATA_PROCESSED_DIR / "preprocessed_data.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T011 (diverse dataset) has been executed.")

    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)

    # Validate required columns
    if 'smiles' not in df.columns:
        raise ValueError("Input dataset must contain a 'smiles' column.")

    logger.info(f"Processing {len(df)} molecules...")
    results = []

    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            logger.info(f"Processed {idx}/{len(df)} molecules")

        smiles = row['smiles']
        contribs = compute_crippen_contributions(smiles)
        contribs['smiles'] = smiles
        # Preserve original experimental values if they exist
        for col in df.columns:
            if col not in contribs:
                contribs[col] = row[col]
        results.append(contribs)

    logger.info("Conversion complete.")
    return pd.DataFrame(results)


def save_predictions(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Save the predictions to a CSV file.

    Args:
        df: DataFrame with predictions.
        output_path: Path to save the CSV. Defaults to data/derived/baseline_predictions.csv.
    """
    if output_path is None:
        output_path = DATA_DERIVED_DIR / "baseline_predictions.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")


def main() -> None:
    """Main entry point for the baseline prediction pipeline."""
    logger.info("Starting Crippen baseline prediction pipeline.")

    try:
        # 1. Process dataset and compute contributions
        df_predictions = process_dataset()

        # 2. Save results
        save_predictions(df_predictions)

        logger.info("Baseline prediction pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()