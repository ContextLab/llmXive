"""
Data preprocessing module for molecular property prediction.

This module handles data loading, missing value handling, diversity filtering,
and train/test splitting.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Import seed manager for reproducibility
from ..seed_manager import set_global_seed, get_seed

# Setup logger
logger = logging.getLogger(__name__)

def load_preprocessed_data(input_path: str) -> pd.DataFrame:
    """
    Load the raw dataset fetched in T008.
    Expects a CSV or Parquet file with at least 'smiles' and target property columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.parquet':
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def filter_high_confidence(df: pd.DataFrame, threshold: float = 0.9) -> pd.DataFrame:
    """
    Filter for high-confidence measurements.
    Assumes a 'confidence' or 'quality_score' column exists.
    If missing, returns the full dataframe (log warning).
    """
    conf_col = None
    for col in ['confidence', 'quality_score', 'measurement_uncertainty']:
        if col in df.columns:
            conf_col = col
            break
    
    if conf_col is None:
        logger.warning("No confidence/quality column found. Skipping high-confidence filter.")
        return df
    
    # If uncertainty column exists, invert it (lower uncertainty = higher confidence)
    if conf_col == 'measurement_uncertainty':
        # Assuming uncertainty is a value where lower is better.
        # We'll define confidence as 1 / (1 + uncertainty) or similar if needed,
        # but for now, let's assume the source provides a direct confidence score 0-1.
        # If it's raw uncertainty, we need a heuristic. Let's assume for T008 source
        # it might be a score. If not, we skip or treat as high confidence if NaN.
        # Based on T031, we check for status. Let's assume if it exists, it's numeric.
        # Heuristic: confidence = 1.0 if uncertainty is missing/NaN, else 1/(1+uncertainty)
        if df[conf_col].dtype in ['float64', 'int64']:
            df['confidence_score'] = 1.0 / (1.0 + df[conf_col].fillna(0))
            conf_col = 'confidence_score'
        else:
            logger.warning("measurement_uncertainty found but not numeric. Skipping filter.")
            return df

    # Filter
    initial_count = len(df)
    df = df[df[conf_col] >= threshold].reset_index(drop=True)
    logger.info(f"Filtered high confidence: {initial_count} -> {len(df)} (threshold={threshold})")
    return df

def handle_missing_values(df: pd.DataFrame, target_cols: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Handle missing values in target columns.
    Rows with missing targets are excluded.
    Returns the filtered dataframe and a list of excluded SMILES (for logging).
    """
    initial_count = len(df)
    # Drop rows where any target column is NaN
    df = df.dropna(subset=target_cols)
    excluded_count = initial_count - len(df)
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} rows due to missing target values.")
    return df

def detect_missing_covariates(df: pd.DataFrame, required_covariates: List[str] = ['temperature', 'pH']) -> pd.DataFrame:
    """
    Detect missing covariates.
    Adds a column 'missing_covariate_list' containing a list of missing covariate names for each row.
    If a required covariate column does not exist in the dataset, it is considered "missing" for all rows.
    """
    # Identify which required columns actually exist in the dataframe
    existing_cols = set(df.columns)
    missing_in_schema = [col for col in required_covariates if col not in existing_cols]
    
    # If a column is missing from schema entirely, we can't check row-wise values,
    # but per FR-008, we must detect missing covariates. If the column doesn't exist,
    # it's effectively missing for every entry.
    
    # Prepare the list column
    def get_missing_list(row):
        missing = []
        for col in required_covariates:
            if col not in existing_cols:
                missing.append(col)
            elif pd.isna(row.get(col)):
                missing.append(col)
        return missing
    
    df['missing_covariate_list'] = df.apply(get_missing_list, axis=1)
    return df

def generate_quality_report(df: pd.DataFrame, target_cols: List[str]) -> pd.DataFrame:
    """
    Generate the data quality report.
    Identifies rows to be excluded based on:
    1. Missing target values (handled in handle_missing_values, but we log them here if not already dropped)
    2. Missing covariates (any row with a non-empty missing_covariate_list)
    
    Returns a DataFrame with columns: smiles, exclusion_reason, missing_covariate_list
    """
    # We assume 'smiles' is always present
    if 'smiles' not in df.columns:
        raise ValueError("Input dataframe must contain 'smiles' column")

    report_rows = []

    for idx, row in df.iterrows():
        reasons = []
        missing_covs = row.get('missing_covariate_list', [])
        
        # Check for missing targets
        for col in target_cols:
            if pd.isna(row.get(col)):
                reasons.append(f"missing_target_{col}")
        
        # Check for missing covariates
        if missing_covs:
            reasons.append("missing_covariates")
        
        if reasons:
            report_rows.append({
                'smiles': row['smiles'],
                'exclusion_reason': '; '.join(reasons),
                'missing_covariate_list': str(missing_covs) # Convert list to string for CSV storage
            })
    
    report_df = pd.DataFrame(report_rows)
    return report_df

def save_quality_report(report_df: pd.DataFrame, output_path: str):
    """
    Save the quality report to CSV.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(path, index=False)
    logger.info(f"Saved quality report to {output_path} with {len(report_df)} entries")

def tanimoto_similarity(fp1: np.ndarray, fp2: np.ndarray) -> float:
    """
    Calculate Tanimoto similarity between two bit vectors.
    """
    intersection = np.logical_and(fp1, fp2).sum()
    union = np.logical_or(fp1, fp2).sum()
    if union == 0:
        return 0.0
    return float(intersection) / union

def maxmin_sampling(smiles_list: List[str], fingerprints: np.ndarray, target_size: int = 4000, seed: Optional[int] = None) -> List[int]:
    """
    Perform MaxMin sampling to select a diverse subset of molecules.
    Selects the first molecule randomly, then iteratively selects the molecule
    that maximizes the minimum distance to the already selected set.
    Returns indices of selected molecules.
    """
    if seed is not None:
        set_global_seed(seed)
    
    n_total = len(smiles_list)
    if n_total <= target_size:
        logger.info(f"Total molecules ({n_total}) <= target size ({target_size}). Returning all.")
        return list(range(n_total))
    
    logger.info(f"Starting MaxMin sampling: {n_total} -> {target_size}")
    
    # Initialize
    selected_indices = [np.random.randint(n_total)]
    remaining_indices = [i for i in range(n_total) if i != selected_indices[0]]
    
    # Precompute distances? For O(N^2) it might be heavy, but we need to be careful with memory.
    # Given the constraint of 4000, we can compute distances on the fly or cache.
    # Let's compute distances from selected to remaining iteratively.
    
    # Current min distances for each remaining point to the selected set
    # Initialize with distance to the first selected point
    min_dists = np.full(n_total, -1.0)
    
    # We only care about remaining points
    # Let's track the min distance to the selected set for each remaining index
    # Initialize with distance to first selected
    first_fp = fingerprints[selected_indices[0]]
    for idx in remaining_indices:
        min_dists[idx] = 1.0 - tanimoto_similarity(first_fp, fingerprints[idx]) # Distance = 1 - Sim
    
    for _ in range(target_size - 1):
        # Find the point with the maximum min-distance
        # We only look at remaining_indices
        best_idx = -1
        best_dist = -1.0
        
        for idx in remaining_indices:
            if min_dists[idx] > best_dist:
                best_dist = min_dists[idx]
                best_idx = idx
        
        if best_idx == -1:
            break
        
        # Add best_idx to selected
        selected_indices.append(best_idx)
        remaining_indices.remove(best_idx)
        
        # Update min distances for remaining points
        new_fp = fingerprints[best_idx]
        for idx in remaining_indices:
            dist = 1.0 - tanimoto_similarity(new_fp, fingerprints[idx])
            if dist < min_dists[idx] or min_dists[idx] == -1.0:
                min_dists[idx] = dist
    
    logger.info(f"MaxMin sampling complete. Selected {len(selected_indices)} molecules.")
    return selected_indices

def save_processed_data(df: pd.DataFrame, output_path: str):
    """
    Save the processed dataframe to CSV/Parquet.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == '.parquet':
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)
    logger.info(f"Saved processed data to {output_path}")

def maxmin_sampling(
    smiles_list: List[str],
    target_size: int = 5000,
    similarity_threshold: float = 0.7,
    fingerprint_radius: int = 2,
    fingerprint_size: int = 2048
) -> List[str]:
    """
    Main execution flow for T009:
    1. Load raw data (from T008 output)
    2. Filter high confidence
    3. Handle missing targets
    4. Detect missing covariates
    5. Generate and save quality report
    """
    # Configuration
    INPUT_PATH = "data/raw/thermodynamics_raw.csv" # Adjust based on T008 output
    OUTPUT_REPORT_PATH = "data/derived/data_quality_report.csv"
    TARGET_COLS = ['logP', 'solubility', 'boiling_point'] # Adjust based on actual data schema
    REQUIRED_COVARIATES = ['temperature', 'pH']
    
    # Check if input exists (T008 should have created it)
    if not Path(INPUT_PATH).exists():
        # Try to find parquet
        p_path = INPUT_PATH.replace('.csv', '.parquet')
        if Path(p_path).exists():
            INPUT_PATH = p_path
        else:
            logger.error(f"Input data not found at {INPUT_PATH}. Please run T008 first.")
            sys.exit(1)

    set_global_seed(42)
    
    # 1. Load
    df = load_preprocessed_data(INPUT_PATH)
    
    # 2. Filter high confidence
    df = filter_high_confidence(df)
    
    # 3. Detect missing covariates (before dropping rows based on them, we need to log them)
    df = detect_missing_covariates(df, REQUIRED_COVARIATES)
    
    # 4. Handle missing targets (this drops rows, but we need to report them)
    # We generate the report BEFORE dropping, so we capture the reason
    report_df = generate_quality_report(df, TARGET_COLS)
    save_quality_report(report_df, OUTPUT_REPORT_PATH)
    
    # Now drop the rows for the next steps (T010/T011)
    df = handle_missing_values(df, TARGET_COLS)
    
    # 5. Save cleaned data for next tasks
    cleaned_path = "data/derived/cleaned_data.csv"
    save_processed_data(df, cleaned_path)
    
    logger.info("T009 Preprocessing complete.")

if __name__ == "__main__":
    main()