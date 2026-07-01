"""
T016: Generate data/curated/curated_dataset.csv with complete molecular graph structures and adhesion energy measurements.

This script reads the cleaned and validated data from the previous step (T014/T015),
constructs the final curated dataset including molecular graph representations
(using RDKit to generate canonical SMILES and basic graph properties), and saves it
to data/curated/curated_dataset.csv.

It relies on the outputs of T011 (download), T013 (hard abort check), T014 (cleaning),
and T015 (power analysis warning).
"""

import os
import sys
import logging
import json
import math
from pathlib import Path
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.exceptions import DataError
from utils.logger import PerformanceLogger, log_performance
from utils.seed_utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """Load the cleaned dataset from the previous step."""
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. "
                                "Please ensure T014 (clean.py) has run successfully.")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def compute_graph_properties(smiles: str) -> dict:
    """
    Compute basic graph properties for a given SMILES string.
    Returns a dictionary with:
      - num_atoms: number of atoms
      - num_bonds: number of bonds
      - molecular_weight: MW
      - logp: LogP
      - num_rotatable_bonds: Rotatable bonds
      - num_h_acceptors: H-bond acceptors
      - num_h_donors: H-bond donors
      - topological_polar_surface_area: TPSA
      - canonical_smiles: Canonical SMILES representation
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {
            "num_atoms": 0,
            "num_bonds": 0,
            "molecular_weight": 0.0,
            "logp": 0.0,
            "num_rotatable_bonds": 0,
            "num_h_acceptors": 0,
            "num_h_donors": 0,
            "topological_polar_surface_area": 0.0,
            "canonical_smiles": None
        }

    try:
        canonical_smiles = Chem.MolToSmiles(mol)
        num_atoms = mol.GetNumAtoms()
        num_bonds = mol.GetNumBonds()
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        rotatable = Descriptors.NumRotatableBonds(mol)
        h_acc = Descriptors.NumHAcceptors(mol)
        h_don = Descriptors.NumHDonors(mol)
        tpsa = Descriptors.TPSA(mol)

        return {
            "num_atoms": num_atoms,
            "num_bonds": num_bonds,
            "molecular_weight": mw,
            "logp": logp,
            "num_rotatable_bonds": rotatable,
            "num_h_acceptors": h_acc,
            "num_h_donors": h_don,
            "topological_polar_surface_area": tpsa,
            "canonical_smiles": canonical_smiles
        }
    except Exception as e:
        logger.warning(f"Error computing properties for SMILES {smiles}: {e}")
        return {
            "num_atoms": 0,
            "num_bonds": 0,
            "molecular_weight": 0.0,
            "logp": 0.0,
            "num_rotatable_bonds": 0,
            "num_h_acceptors": 0,
            "num_h_donors": 0,
            "topological_polar_surface_area": 0.0,
            "canonical_smiles": None
        }

def generate_curated_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate the curated dataset by adding graph properties for polymer and filler.
    """
    logger.info("Computing graph properties for polymer and filler molecules...")
    
    # Apply graph property computation to polymer and filler SMILES columns
    # Assuming the cleaned data has 'polymer_smiles' and 'filler_smiles' columns
    if 'polymer_smiles' not in df.columns or 'filler_smiles' not in df.columns:
        raise DataError("Missing required columns 'polymer_smiles' or 'filler_smiles' in cleaned data.")

    polymer_props = df['polymer_smiles'].apply(lambda x: compute_graph_properties(str(x)) if pd.notna(x) else compute_graph_properties(""))
    filler_props = df['filler_smiles'].apply(lambda x: compute_graph_properties(str(x)) if pd.notna(x) else compute_graph_properties(""))

    # Flatten the dictionaries into separate columns
    polymer_cols = {f"polymer_{k}": [p[k] for p in polymer_props] for k in polymer_props[0].keys()}
    filler_cols = {f"filler_{k}": [f[k] for f in filler_props] for f in filler_props[0].keys()}

    # Add new columns to the dataframe
    for col_name, values in polymer_cols.items():
        df[col_name] = values
    for col_name, values in filler_cols.items():
        df[col_name] = values

    logger.info(f"Generated {len(df.columns)} columns in curated dataset.")
    return df

def main():
    """Main entry point for T016."""
    # Set seed for reproducibility
    set_seed(42)

    # Define paths
    cleaned_data_path = project_root / "data" / "curated" / "cleaned_dataset.csv"
    output_dir = project_root / "data" / "curated"
    output_path = output_dir / "curated_dataset.csv"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting T016: Generate curated dataset...")
    
    try:
        # Load cleaned data
        df = load_cleaned_data(cleaned_data_path)

        # Check row count (should already be validated by T013/T014)
        if len(df) < 100:
            raise DataError(f"Dataset has {len(df)} rows, which is less than the required minimum of 100. "
                            "This should have been caught by T013.")

        # Generate curated dataset with graph properties
        curated_df = generate_curated_dataset(df)

        # Save to CSV
        curated_df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved curated dataset to {output_path}")
        logger.info(f"Total rows: {len(curated_df)}, Total columns: {len(curated_df.columns)}")

        # Log performance
        log_performance("T016_generate_curated", output_path, len(curated_df))

    except Exception as e:
        logger.error(f"Error during T016 execution: {e}")
        raise

if __name__ == "__main__":
    main()