import os
import sys
import logging
import itertools
from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

def load_pinned_real_sample(filepath: str, n_rows: int = 5) -> pd.DataFrame:
    """Loads a small sample of the real dataset for robustness testing."""
    try:
        df = pd.read_csv(filepath)
        return df.head(n_rows).copy()  # Return a copy to avoid modifying original data
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        raise
    except Exception as e:
        logging.error(f"Error loading dataset: {e}")
        raise

def run_robustness_checks(df: pd.DataFrame) -> None:
    """Runs basic robustness checks on the loaded DataFrame."""
    if df.empty:
        logging.warning("DataFrame is empty. Skipping robustness checks.")
        return

    # Check for valid SMILES strings
    invalid_smiles = []
    for index, row in df.iterrows():
        try:
            mol = Chem.MolFromSmiles(row['SMILES'])
            if mol is None:
                invalid_smiles.append(index)
        except Exception as e:
            logging.error(f"Error processing SMILES at index {index}: {e}")  # Log error and continue processing other rows
            invalid_smiles.append(index)

    if invalid_smiles:
        logging.warning(f"Invalid SMILES found at indices: {invalid_smiles}")

    # Calculate descriptors for the first molecule to test RDKit stability
    try:
        mol = Chem.MolFromSmiles(df['SMILES'].iloc[0])  # Access the first row's 'SMILES' column
        if mol is not None:
            Descriptors.MolWt(mol)
            Descriptors.TPSA(mol)
            Descriptors.LogP(mol)

    except Exception as e:
        logging.error(f"Error calculating descriptors: {e}")

def main():
    """Main function to load data and run robustness checks."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        data_path = "data/processed/structural_subset.csv"  # Or your actual path to the dataset
        df = load_pinned_real_sample(data_path, n_rows=5)
        run_robustness_checks(df)

    except Exception as e:
        logging.error(f"An error occurred during robustness testing: {e}")
        sys.exit(1)  # Exit with an error code if there's a problem


if __name__ == "__main__":
    main()