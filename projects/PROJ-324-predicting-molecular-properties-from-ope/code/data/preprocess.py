"""
Data preprocessing module for molecular property prediction.

This module handles data loading, missing value handling, diversity filtering,
and train/test splitting.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit import DataStructs
from rdkit.Chem.AllChem import GetMorganFingerprintAsBitVect

# Configure logging
logger = logging.getLogger(__name__)

def load_preprocessed_data(raw_path: str) -> pd.DataFrame:
    """
    Load raw data and perform initial cleaning.

    Args:
        raw_path: Path to the raw data file.

    Returns:
        Cleaned DataFrame.
    """
    df = pd.read_csv(raw_path)
    # Remove rows with invalid SMILES
    valid_indices = []
    for idx, smiles in enumerate(df['smiles']):
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            valid_indices.append(idx)

    df = df.iloc[valid_indices].reset_index(drop=True)
    logger.info(f"Loaded {len(df)} valid molecules")
    return df

def detect_missing_covariates(df: pd.DataFrame, covariate_columns: List[str]) -> pd.Series:
    """
    Detect missing values in covariate columns.

    Args:
        df: Input DataFrame.
        covariate_columns: List of covariate column names.

    Returns:
        Series indicating missing covariates for each row.
    """
    missing_flags = df[covariate_columns].isnull().any(axis=1)
    return missing_flags

def handle_missing_values(
    df: pd.DataFrame,
    target_columns: List[str],
    covariate_columns: List[str]
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Handle missing values by dropping rows with missing targets and flagging missing covariates.

    Args:
        df: Input DataFrame.
        target_columns: List of target column names.
        covariate_columns: List of covariate column names.

    Returns:
        Tuple of (cleaned DataFrame, list of excluded entries).
    """
    excluded_entries = []

    # Drop rows with missing target values
    mask_targets = df[target_columns].isnull().any(axis=1)
    excluded_reasons = df[mask_targets].apply(lambda row: {
        'smiles': row['smiles'],
        'exclusion_reason': 'missing_target',
        'missing_covariate_list': []
    }, axis=1).tolist()
    excluded_entries.extend(excluded_reasons)

    df_clean = df[~mask_targets].copy()

    # Flag missing covariates (but don't drop)
    mask_covariates = df_clean[covariate_columns].isnull().any(axis=1)
    covariate_flags = df_clean[mask_covariates][covariate_columns].isnull()
    missing_covariate_list = covariate_flags.apply(
        lambda row: list(row[row].index), axis=1
    ).tolist()

    excluded_reasons = df_clean[mask_covariates].apply(lambda row: {
        'smiles': row['smiles'],
        'exclusion_reason': 'missing_covariate',
        'missing_covariate_list': missing_covariate_list
    }, axis=1).tolist()
    excluded_entries.extend(excluded_reasons)

    logger.info(f"Dropped {mask_targets.sum()} rows with missing targets")
    logger.info(f"Flagged {mask_covariates.sum()} rows with missing covariates")

    return df_clean, excluded_entries

def generate_quality_report(excluded_entries: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a data quality report for excluded entries.

    Args:
        excluded_entries: List of excluded entry dictionaries.
        output_path: Path to save the report.
    """
    report_df = pd.DataFrame(excluded_entries)
    report_df.to_csv(output_path, index=False)
    logger.info(f"Quality report saved to {output_path}")

def save_quality_report(report_df: pd.DataFrame, output_path: str) -> None:
    """
    Save the quality report to disk.

    Args:
        report_df: DataFrame with quality report data.
        output_path: Path to save the report.
    """
    report_df.to_csv(output_path, index=False)

def filter_high_confidence(df: pd.DataFrame, confidence_threshold: float = 0.8) -> pd.DataFrame:
    """
    Filter for high-confidence measurements.

    Args:
        df: Input DataFrame.
        confidence_threshold: Minimum confidence score.

    Returns:
        Filtered DataFrame.
    """
    if 'confidence' in df.columns:
        df = df[df['confidence'] >= confidence_threshold]
    logger.info(f"Filtered to {len(df)} high-confidence molecules")
    return df

def save_processed_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save processed data to disk.

    Args:
        df: Processed DataFrame.
        output_path: Path to save the data.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")

def tanimoto_similarity(fp1: DataStructs.ExplicitBitVect, fp2: DataStructs.ExplicitBitVect) -> float:
    """
    Calculate Tanimoto similarity between two fingerprints.

    Args:
        fp1: First fingerprint.
        fp2: Second fingerprint.

    Returns:
        Tanimoto similarity score.
    """
    return DataStructs.TanimotoSimilarity(fp1, fp2)

def maxmin_sampling(
    smiles_list: List[str],
    target_size: int = 5000,
    similarity_threshold: float = 0.7,
    fingerprint_radius: int = 2,
    fingerprint_size: int = 2048
) -> List[str]:
    """
    Select a diverse subset of molecules using MaxMin sampling.

    Args:
        smiles_list: List of SMILES strings.
        target_size: Target number of molecules.
        similarity_threshold: Maximum allowed Tanimoto similarity.
        fingerprint_radius: Radius for Morgan fingerprint.
        fingerprint_size: Size of the fingerprint.

    Returns:
        List of selected SMILES strings.
    """
    logger.info(f"Starting MaxMin sampling for {len(smiles_list)} molecules, target: {target_size}")

    # Convert SMILES to fingerprints
    fps = []
    valid_smiles = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            fp = GetMorganFingerprintAsBitVect(mol, radius=fingerprint_radius, nBits=fingerprint_size)
            fps.append(fp)
            valid_smiles.append(smiles)

    if len(fps) == 0:
        logger.warning("No valid molecules found")
        return []

    selected_indices = [0]  # Start with first molecule
    remaining_indices = list(range(1, len(fps)))

    while len(selected_indices) < target_size and remaining_indices:
        # Calculate min distance from each remaining molecule to selected set
        min_distances = []
        for i in remaining_indices:
            max_sim = 0
            for j in selected_indices:
                sim = tanimoto_similarity(fps[i], fps[j])
                max_sim = max(max_sim, sim)
            min_distances.append((i, 1 - max_sim))  # Distance = 1 - similarity

        # Sort by distance (descending) and pick the farthest
        min_distances.sort(key=lambda x: x[1], reverse=True)

        # Check if the farthest is still too similar
        if min_distances[0][1] < (1 - similarity_threshold):
            # All remaining are too similar, stop
            logger.info(f"Reached similarity threshold, stopping with {len(selected_indices)} molecules")
            break

        # Add the farthest molecule
        next_idx = min_distances[0][0]
        selected_indices.append(next_idx)
        remaining_indices.remove(next_idx)

    selected_smiles = [valid_smiles[i] for i in selected_indices]
    logger.info(f"MaxMin sampling complete: {len(selected_smiles)} molecules selected")
    return selected_smiles

def main() -> None:
    """
    Main entry point for the preprocessing pipeline.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    raw_path = project_root / 'data' / 'raw' / 'chembl_thermodynamics.csv'
    output_dir = project_root / 'data' / 'derived'

    if not raw_path.exists():
        logger.error(f"Raw data not found: {raw_path}")
        sys.exit(1)

    # Load data
    logger.info("Loading raw data...")
    df = load_preprocessed_data(str(raw_path))

    # Handle missing values
    target_columns = ['logP', 'solubility', 'boiling_point']
    covariate_columns = ['temperature', 'pH']
    df_clean, excluded_entries = handle_missing_values(df, target_columns, covariate_columns)

    # Generate quality report
    generate_quality_report(excluded_entries, str(output_dir / 'data_quality_report.csv'))

    # Diversity filtering
    logger.info("Performing diversity filtering...")
    selected_smiles = maxmin_sampling(df_clean['smiles'].tolist(), target_size=5000)
    df_diverse = df_clean[df_clean['smiles'].isin(selected_smiles)].reset_index(drop=True)

    # Save processed data
    save_processed_data(df_diverse, str(output_dir / 'diverse_dataset.csv'))

    logger.info("Preprocessing complete")

if __name__ == "__main__":
    main()
