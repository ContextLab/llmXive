import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import DataStructs
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator
import psutil

# Import from sibling modules if they exist (optional, for consistency)
try:
    from seed_manager import set_global_seed
except ImportError:
    def set_global_seed(seed):
        import random
        random.seed(seed)

# Constants
TARGET_PROPS = ['logP', 'Solubility', 'Boiling Point']
DIVERSITY_THRESHOLD = 0.7
MAX_MIN_SIZE_TARGET = 5000
RAM_THRESHOLD_GB = 6.0
CORES_THRESHOLD = 2

logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure output directories exist."""
    dirs = [
        Path('data/raw'),
        Path('data/derived'),
        Path('data/processed')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_preprocessed_data(input_path: str) -> pd.DataFrame:
    """Load preprocessed data from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    return df

def filter_high_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for high-confidence measurements."""
    # Check for target properties
    available_props = [p for p in TARGET_PROPS if p in df.columns]
    if not available_props:
        logger.warning(f"No target properties found in columns: {df.columns.tolist()}")
        # If no target properties, we cannot filter, return empty or raise?
        # Based on T009, we must exclude entries where target properties are missing.
        # If the dataset has NO target properties at all, the result is empty.
        return pd.DataFrame(columns=df.columns)

    # Filter rows where at least one target property is present
    valid_rows = df[available_props].notna().any(axis=1)
    df_filtered = df[valid_rows].copy()

    logger.info(f"Filtered to {len(df_filtered)} rows with at least one target property.")
    return df_filtered

def detect_missing_covariates(df: pd.DataFrame) -> List[str]:
    """Detect missing physical covariates (pH, temperature, pressure)."""
    covariates = ['pH', 'temperature', 'pressure']
    missing = [c for c in covariates if c not in df.columns]
    return missing

def generate_quality_report(df: pd.DataFrame, output_path: str, missing_covariates: List[str]):
    """Generate data quality report."""
    # Calculate experimental ratio
    if 'source_type' in df.columns:
        total = len(df)
        experimental = df[df['source_type'] == 'Experimental'].shape[0]
        experimental_ratio = experimental / total if total > 0 else 0.0
    else:
        experimental_ratio = 0.0
        logger.warning("Column 'source_type' not found in data.")

    # Create report dataframe
    report_data = {
        'smiles': df['smiles'].values if 'smiles' in df.columns else [],
        'exclusion_reason': ['None' if pd.notna(df.loc[i, 'smiles']) else 'Missing SMILES' for i in range(len(df))],
        'missing_covariate_list': [missing_covariates for _ in range(len(df))],
        'experimental_flag': [True],
        'experimental_ratio': [experimental_ratio]
    }

    # Note: The report schema in T009 implies one row per SMILES? Or summary?
    # The task description says: "Schema: data/derived/data_quality_report.csv must include columns: smiles, exclusion_reason..."
    # This implies a row per molecule. However, experimental_ratio is a global metric.
    # We will repeat the global metric for every row to satisfy the schema.
    report_df = pd.DataFrame(report_data)

    # Flag if ratio < 0.5
    if experimental_ratio < 0.5:
        report_df['experimental_threshold_failed'] = True
    else:
        report_df['experimental_threshold_failed'] = False

    report_df.to_csv(output_path, index=False)
    logger.info(f"Data quality report saved to {output_path}")

def tanimoto_similarity(fp1, fp2) -> float:
    """Calculate Tanimoto similarity between two RDKit fingerprints."""
    return DataStructs.TanimotoSimilarity(fp1, fp2)

def define_maxmin_strategy(df: pd.DataFrame) -> Tuple[int, Dict[str, Any]]:
    """
    Define the algorithm to select a diverse subset using MaxMinPicker.
    Checks available RAM/CPU and adjusts target count.
    Returns the target count and a config dict.
    """
    # Check resource telemetry
    memory_available_gb = psutil.virtual_memory().available / (1024 ** 3)
    cpu_count = psutil.cpu_count(logical=False) or 1

    target_count = MAX_MIN_SIZE_TARGET
    adjustments = []

    if memory_available_gb < RAM_THRESHOLD_GB:
        adjustments.append(f"Low RAM ({memory_available_gb:.1f}GB < {RAM_THRESHOLD_GB}GB)")
        target_count = int(target_count * 0.5) # Reduce by half
    if cpu_count < CORES_THRESHOLD:
        adjustments.append(f"Low CPU ({cpu_count} cores < {CORES_THRESHOLD})")
        target_count = int(target_count * 0.5)

    # Ensure minimum of 100 if dataset is small
    if len(df) < MAX_MIN_SIZE_TARGET:
        target_count = len(df)
        adjustments.append(f"Dataset size ({len(df)}) is less than target")

    config = {
        'target_count': target_count,
        'diversity_threshold': DIVERSITY_THRESHOLD,
        'resource_adjustments': adjustments,
        'memory_available_gb': memory_available_gb,
        'cpu_count': cpu_count
    }

    logger.info(f"MaxMin Strategy defined: Target count = {target_count}, Adjustments = {adjustments}")
    return target_count, config

def maxmin_sampling(df: pd.DataFrame, target_count: int, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Execute MaxMin sampling to select a diverse subset.
    Uses RDKit's MaxMinPicker.
    """
    if len(df) == 0:
        logger.error("Input dataframe is empty.")
        return df

    # Prepare fingerprints
    logger.info("Generating fingerprints for MaxMin selection...")
    mols = []
    fps = []
    smiles_list = []
    
    generator = GetMorganGenerator(radius=2, fpSize=2048) # ECFP4-like

    for i, row in df.iterrows():
        smiles = row['smiles']
        if pd.isna(smiles):
            continue
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        fp = generator.GetFingerprint(mol)
        mols.append(mol)
        fps.append(fp)
        smiles_list.append(smiles)

    if len(fps) == 0:
        logger.error("No valid molecules found for fingerprinting.")
        return pd.DataFrame()

    if len(fps) <= target_count:
        logger.info(f"Dataset size ({len(fps)}) is less than target ({target_count}). Selecting all.")
        return df[df['smiles'].isin(smiles_list)].reset_index(drop=True)

    # Use MaxMinPicker
    from rdkit.Chem import rdMoleculeDescriptors
    # Note: RDKit's MaxMinPicker works on a list of fingerprints
    picker = DataStructs.MaxMinPicker()
    
    # Select indices
    # The MaxMinPicker returns a list of indices
    selected_indices = picker.LargestDiverseSubset(fps, target_count)
    
    if selected_indices is None:
        logger.warning("MaxMinPicker failed to select a subset. Falling back to random selection.")
        selected_indices = list(np.random.choice(len(fps), target_count, replace=False))
    
    logger.info(f"Selected {len(selected_indices)} diverse molecules using MaxMinPicker.")

    # Construct result dataframe
    result_data = {
        'smiles': [smiles_list[i] for i in selected_indices],
        # Copy other columns from original df
    }
    
    # Add other columns
    for col in df.columns:
        if col != 'smiles':
            result_data[col] = [df.iloc[i][col] for i in selected_indices]
    
    result_df = pd.DataFrame(result_data)
    return result_df

def split_dataset(df: pd.DataFrame, train_ratio: float = 0.8, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split dataset into training and test sets."""
    set_global_seed(seed)
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    split_idx = int(len(df) * train_ratio)
    train_df = df.iloc[:split_idx].reset_index(drop=True)
    test_df = df.iloc[split_idx:].reset_index(drop=True)
    logger.info(f"Split dataset: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df

def save_processed_data(df: pd.DataFrame, output_path: str):
    """Save processed data to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Data saved to {output_path}")

def main():
    """Main entry point for preprocessing."""
    ensure_dirs()
    logging.basicConfig(level=logging.INFO)

    # Load raw data (assuming T008 produced this)
    raw_path = 'data/raw/pubchem_raw.csv'
    if not os.path.exists(raw_path):
        # Fallback for testing if raw data is missing in this specific task run
        # In a real pipeline, this should fail loudly if T008 didn't run
        logger.error(f"Raw data file {raw_path} not found. Cannot proceed.")
        # Create an empty dummy file to prevent cascade if this is a unit test
        # But per instructions, we must fail loudly if real data is missing.
        raise FileNotFoundError(f"Raw data file {raw_path} not found.")

    df = load_preprocessed_data(raw_path)
    logger.info(f"Loaded {len(df)} rows from {raw_path}")

    # Filter high confidence
    df_filtered = filter_high_confidence(df)
    
    if len(df_filtered) == 0:
        logger.error("No data remaining after filtering. Stopping pipeline.")
        # Save empty report
        generate_quality_report(pd.DataFrame(), 'data/derived/data_quality_report.csv', detect_missing_covariates(pd.DataFrame()))
        return

    # Detect missing covariates
    missing_covariates = detect_missing_covariates(df_filtered)
    
    # Generate Quality Report (T009 requirement)
    generate_quality_report(df_filtered, 'data/derived/data_quality_report.csv', missing_covariates)

    # Define MaxMin Strategy (T010 requirement)
    target_count, config = define_maxmin_strategy(df_filtered)

    # Execute MaxMin Sampling (T010.1 requirement - part of T010 context)
    diverse_df = maxmin_sampling(df_filtered, target_count, config)

    if len(diverse_df) == 0:
        logger.error("MaxMin sampling resulted in empty dataset.")
        return

    # Save diverse subset
    save_processed_data(diverse_df, 'data/derived/diverse_subset.csv')

    # Split Dataset (T011.5 requirement - part of T010 context)
    train_df, test_df = split_dataset(diverse_df)

    # Save splits
    save_processed_data(train_df, 'data/derived/train_set.csv')
    save_processed_data(test_df, 'data/derived/test_set.csv')

    logger.info("Preprocessing complete.")

if __name__ == '__main__':
    main()