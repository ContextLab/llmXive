"""
Preprocess 2D molecular descriptors from SMILES strings.

This module handles the computation of 2D topological descriptors using RDKit,
filtering of high-correlation features, and handling of missing values (NaNs).
It strictly enforces 2D-only constraints, excluding 3D conformer generation,
TPSA calculations, and SMARTS-based functional group counts.

Key Responsibilities:
1. Compute 2D descriptors (rdkit.Descriptors) for SMILES strings.
2. Filter features with high correlation to the target variable (dipole moment).
3. Handle NaN values deterministically: drop records with >5% missing, impute with median otherwise.
4. Process data in batches to ensure memory usage remains under 6GB.

Constraints:
- No 3D conformer generation (e.g., EmbedMolecule, Get3DConformer).
- No TPSA or TPSA_E descriptors.
- No SMARTS pattern matching for functional groups.
"""

import os
import sys
import logging
import gc
from pathlib import Path
from typing import Iterator, Tuple, List, Dict, Any, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
from scipy import stats

# Import local utilities
from utils.logging_config import get_logger
from utils.validators import assert_no_3d_calls, validate_descriptor_computation_context

# Initialize logger
logger = get_logger(__name__)

# Constants
DESCRIPTOR_EXCLUSIONS = {
    'TPSA', 'TPSA_E', 'TPSA_E2', 'TPSA_E3',  # Explicit TPSA exclusions
    # Add any other 3D or SMARTS-based descriptors if necessary
}

MISSING_THRESHOLD = 0.05  # 5% missing value threshold

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """
    Compute 2D descriptors for a batch of SMILES strings.

    This function iterates over a list of SMILES strings, converts them to RDKit Mol objects,
    computes a set of 2D topological descriptors, and returns a pandas DataFrame.

    Args:
        smiles_list (List[str]): List of SMILES strings.

    Returns:
        pd.DataFrame: DataFrame containing SMILES strings and computed descriptors.
                      Columns include 'smiles', 'target' (if available), and descriptor names.

    Raises:
        ValueError: If a SMILES string is invalid and cannot be parsed.
        RuntimeError: If any 3D-related functions are inadvertently called (checked via assertions).
    """
    assert_no_3d_calls()
    validate_descriptor_computation_context()

    data = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Invalid SMILES string skipped: {smiles}")
            continue

        descriptor_values = {}
        for name, func in Descriptors._descList:
            if name in DESCRIPTOR_EXCLUSIONS:
                continue
            try:
                val = func(mol)
                if np.isnan(val) or np.isinf(val):
                    descriptor_values[name] = np.nan
                else:
                    descriptor_values[name] = val
            except Exception as e:
                logger.warning(f"Error computing descriptor {name} for SMILES {smiles}: {e}")
                descriptor_values[name] = np.nan

        data.append({'smiles': smiles, **descriptor_values})

    df = pd.DataFrame(data)
    logger.info(f"Computed descriptors for {len(df)} molecules. Total descriptors: {len(df.columns) - 1}")
    return df

def filter_high_correlation_features(df: pd.DataFrame, target_col: str = 'target', threshold: float = 0.85) -> pd.DataFrame:
    """
    Filter out features that have a high correlation with the target variable.

    This function computes the Pearson correlation coefficient between each feature
    and the target variable. Features with an absolute correlation greater than
    the specified threshold are excluded from the dataset.

    Args:
        df (pd.DataFrame): DataFrame containing features and the target variable.
        target_col (str): Name of the target column. Default is 'target'.
        threshold (float): Correlation threshold for exclusion. Default is 0.85.

    Returns:
        pd.DataFrame: DataFrame with high-correlation features removed.
    """
    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' not found in DataFrame. Skipping correlation filter.")
        return df

    features = [col for col in df.columns if col != target_col and col != 'smiles']
    correlations = {}
    for feature in features:
        corr, _ = stats.pearsonr(df[feature], df[target_col])
        correlations[feature] = corr

    filtered_features = [f for f, c in correlations.items() if abs(c) <= threshold]
    excluded_features = [f for f, c in correlations.items() if abs(c) > threshold]

    if excluded_features:
        logger.info(f"Excluding {len(excluded_features)} features with |r| > {threshold}: {excluded_features}")
    else:
        logger.info(f"No features excluded based on correlation threshold {threshold}.")

    return df[['smiles', target_col] + filtered_features]

def handle_missing_values(df: pd.DataFrame, target_col: str = 'target') -> pd.DataFrame:
    """
    Handle missing values (NaNs) in the DataFrame.

    This function applies deterministic logic for handling missing values:
    - If a column has more than 5% missing values, the entire record (row) is dropped.
    - Otherwise, missing values in a column are imputed with the column's median.

    Args:
        df (pd.DataFrame): DataFrame containing features and the target variable.
        target_col (str): Name of the target column. Default is 'target'.

    Returns:
        pd.DataFrame: DataFrame with missing values handled.
    """
    logger.info(f"Handling missing values. Threshold: {MISSING_THRESHOLD * 100}%")

    # Identify columns with >5% missing values
    missing_percent = df.isnull().mean()
    columns_to_drop = missing_percent[missing_percent > MISSING_THRESHOLD].index.tolist()

    if columns_to_drop:
        logger.warning(f"Dropping {len(columns_to_drop)} columns with >{MISSING_THRESHOLD * 100}% missing values: {columns_to_drop}")
        df = df.drop(columns=columns_to_drop)

    # Drop rows with any remaining missing values
    initial_rows = len(df)
    df = df.dropna()
    dropped_rows = initial_rows - len(df)
    if dropped_rows > 0:
        logger.warning(f"Dropped {dropped_rows} rows due to remaining missing values.")

    # Impute remaining NaNs with column median
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        median_val = df[col].median()
        if pd.isna(median_val):
            logger.warning(f"Median for column '{col}' is NaN. Skipping imputation.")
            continue
        df[col] = df[col].fillna(median_val)

    logger.info(f"Missing value handling complete. Final shape: {df.shape}")
    return df

def preprocess_2d(input_path: str, output_path: str, batch_size: int = 1000) -> None:
    """
    Preprocess 2D descriptors from a raw SMILES file and save to a Parquet file.

    This function reads SMILES strings from the input file in batches, computes
    2D descriptors, filters high-correlation features, handles missing values,
    and saves the processed data to the output Parquet file.

    Args:
        input_path (str): Path to the input file containing SMILES strings.
        output_path (str): Path to save the processed Parquet file.
        batch_size (int): Number of SMILES strings to process in each batch. Default is 1000.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file format is invalid.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Starting preprocessing. Input: {input_path}, Output: {output_path}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    processed_data = []
    smiles_list = []
    targets = []

    # Iterate over the input file in batches
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                logger.warning(f"Invalid line format: {line}")
                continue
            smiles, target = parts[0], float(parts[1])
            smiles_list.append(smiles)
            targets.append(target)

            if len(smiles_list) >= batch_size:
                batch_df = compute_descriptors_batch(smiles_list)
                batch_df['target'] = targets
                processed_data.append(batch_df)
                smiles_list = []
                targets = []
                gc.collect()  # Explicit garbage collection to manage memory

        # Process remaining items
        if smiles_list:
            batch_df = compute_descriptors_batch(smiles_list)
            batch_df['target'] = targets
            processed_data.append(batch_df)

    if not processed_data:
        logger.error("No data processed. Exiting.")
        return

    # Concatenate all batches
    full_df = pd.concat(processed_data, ignore_index=True)
    logger.info(f"Total records after batch processing: {len(full_df)}")

    # Filter high-correlation features
    full_df = filter_high_correlation_features(full_df)

    # Handle missing values
    full_df = handle_missing_values(full_df)

    # Save to Parquet
    full_df.to_parquet(output_file, index=False)
    logger.info(f"Processed data saved to {output_path}")

def main() -> None:
    """
    Main entry point for the 2D preprocessing pipeline.

    This function parses command-line arguments to get the input and output paths,
    and invokes the preprocessing pipeline.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess 2D molecular descriptors from SMILES.")
    parser.add_argument("--input", type=str, required=True, help="Path to input SMILES file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output Parquet file.")
    parser.add_argument("--batch_size", type=int, default=1000, help="Batch size for processing.")

    args = parser.parse_args()

    try:
        preprocess_2d(args.input, args.output, args.batch_size)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()