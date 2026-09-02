"""
Data Ingestion Module for Molecular Properties Prediction Pipeline.

This script fetches the ESOL dataset from MoleculeNet, validates the schema,
performs power analysis, enforces scaffold diversity checks, and ensures
reproducibility via random seed pinning.

Output:
    data/processed/esol_raw.csv: Validated dataset with 'smiles' and 'logP' columns.
    data/logs/ingestion.log: Detailed logging of the ingestion process.
"""
import os
import sys
import logging
import random
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
RANDOM_SEED = 42
MIN_SAMPLES_POWER = 128
MIN_SCAFFOLDS_RATIO = 0.05  # At least 5% unique scaffolds relative to N
ESOL_URL = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv"
OUTPUT_FILE = DATA_PROCESSED_DIR / "esol_raw.csv"
LOG_FILE = LOGS_DIR / "ingestion.log"

def setup_logging() -> logging.Logger:
    """Configure logging for the ingestion process."""
    logger = logging.getLogger("esol_ingestion")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def fetch_esol_dataset(logger: logging.Logger) -> pd.DataFrame:
    """
    Fetch the ESOL dataset from the real source (DeepChem S3 bucket).
    Falls back to no synthetic data; raises error if fetch fails.
    """
    import requests

    logger.info(f"Fetching ESOL dataset from: {ESOL_URL}")
    try:
        response = requests.get(ESOL_URL, timeout=60)
        response.raise_for_status()
        # Parse CSV from text content
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        logger.info(f"Successfully fetched {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise RuntimeError(f"Could not retrieve real ESOL data. Aborting. Error: {e}")

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate that the dataframe contains 'smiles' and 'logP' (or 'measured logP') columns.
    Standardizes column names if necessary.
    """
    required_cols = ['smiles', 'logP']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    # Handle common variations
    if 'measured logP' in df.columns and 'logP' not in df.columns:
        df = df.rename(columns={'measured logP': 'logP'})
        missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}. Available: {df.columns.tolist()}")

    # Drop rows with missing critical values
    initial_len = len(df)
    df = df.dropna(subset=['smiles', 'logP'])
    dropped = initial_len - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to missing SMILES or logP values.")

    logger.info(f"Schema validation passed. {len(df)} valid rows.")
    return df, missing_cols

def perform_power_analysis(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Perform a priori power analysis check.
    Ensures N >= MIN_SAMPLES_POWER.
    """
    n = len(df)
    logger.info(f"Performing power analysis: N = {n} (Minimum required: {MIN_SAMPLES_POWER})")
    if n < MIN_SAMPLES_POWER:
        raise ValueError(f"Sample size {n} is below the minimum power threshold of {MIN_SAMPLES_POWER}.")
    logger.info("Power analysis passed.")
    return True

def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    """Extract Bemis-Murcko scaffold SMILES from a molecule SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception:
        return None

def enforce_scaffold_check(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Enforce minimum scaffold diversity.
    Checks if unique scaffolds >= MIN_SCAFFOLDS_RATIO * N.
    """
    logger.info("Computing Bemis-Murcko scaffolds for diversity check...")
    scaffolds = df['smiles'].apply(get_bemis_murcko_scaffold)
    # Filter out None results (invalid molecules)
    valid_scaffolds = scaffolds.dropna()
    unique_scaffolds = valid_scaffolds.unique()
    n_unique = len(unique_scaffolds)
    n_total = len(df)
    
    ratio = n_unique / n_total if n_total > 0 else 0
    min_required = MIN_SCAFFOLDS_RATIO * n_total

    logger.info(f"Total molecules: {n_total}, Unique scaffolds: {n_unique}, Ratio: {ratio:.4f}")
    
    if n_unique < min_required:
        raise ValueError(
            f"Scaffold diversity insufficient. Found {n_unique} unique scaffolds. "
            f"Minimum required: {min_required:.0f} (Ratio: {MIN_SCAFFOLDS_RATIO})."
        )
    
    logger.info("Scaffold diversity check passed.")
    return True

def pin_random_seed(seed: int = RANDOM_SEED) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    # RDKit random seed
    try:
        from rdkit import Random
        Random.seed(seed)
    except Exception:
        pass
    os.environ['PYTHONHASHSEED'] = str(seed)
    logging.getLogger().info(f"Random seed pinned to {seed}.")

def main():
    """Main execution pipeline for data ingestion."""
    logger = setup_logging()
    logger.info("Starting ESOL Data Ingestion Pipeline.")

    try:
        # 1. Pin seeds first
        pin_random_seed(RANDOM_SEED)

        # 2. Fetch Real Data
        df = fetch_esol_dataset(logger)

        # 3. Validate Schema
        df, _ = validate_schema(df, logger)

        # 4. Power Analysis
        perform_power_analysis(df, logger)

        # 5. Scaffold Diversity Check
        enforce_scaffold_check(df, logger)

        # 6. Save Output
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Data ingestion complete. Output saved to: {OUTPUT_FILE}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
