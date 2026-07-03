import pandas as pd
import hashlib
import logging
import os
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from src.data.schemas import FeatureVector
from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import register_artifact, get_state
from src.modeling.config import load_config

# Initialize logger
logger = get_logger(__name__)

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Compute the checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_feature_matrix(
    feature_df: pd.DataFrame,
    output_path: str,
    checksum_path: Optional[str] = None
) -> Tuple[str, str]:
    """
    Save the feature matrix to a Parquet file and compute its checksum.
    
    Args:
        feature_df: The DataFrame containing the feature matrix.
        output_path: The path where the Parquet file will be saved.
        checksum_path: Optional path to save the checksum file.
    
    Returns:
        A tuple containing the output path and the checksum string.
    """
    if feature_df is None or feature_df.empty:
        raise ValueError("Feature DataFrame is empty or None.")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to Parquet
    feature_df.to_parquet(output_path, index=False, engine='pyarrow')
    logger.info(f"Feature matrix saved to {output_path}")
    
    # Compute checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Checksum computed: {checksum}")
    
    # Save checksum if path provided
    if checksum_path:
        checksum_dir = os.path.dirname(checksum_path)
        if checksum_dir:
            os.makedirs(checksum_dir, exist_ok=True)
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        logger.info(f"Checksum saved to {checksum_path}")
    
    return output_path, checksum

def load_feature_matrix(input_path: str) -> pd.DataFrame:
    """
    Load the feature matrix from a Parquet file.
    
    Args:
        input_path: The path to the Parquet file.
    
    Returns:
        The loaded DataFrame.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Feature matrix file not found: {input_path}")
    
    df = pd.read_parquet(input_path, engine='pyarrow')
    logger.info(f"Loaded feature matrix from {input_path} with shape {df.shape}")
    return df

def preprocess_and_save_features(
    input_csv_path: str,
    output_parquet_path: str,
    config: Optional[dict] = None
) -> dict:
    """
    Load filtered reactions, extract features, reduce dimensionality, 
    and save the resulting feature matrix to Parquet with checksum.
    
    This function assumes that T021 (feature extraction) and T023 (dimensionality reduction)
    have already been implemented in `src/data/preprocessing.py` as helper functions 
    or that the input CSV already contains the reduced feature set. 
    
    For this task (T024), we focus on saving the feature matrix. 
    We assume the input CSV (`data/processed/filtered_reactions.csv`) contains 
    the necessary columns including the reduced feature set (columns starting with 'feat_').
    
    Args:
        input_csv_path: Path to the filtered reactions CSV.
        output_parquet_path: Path to save the feature matrix Parquet file.
        config: Configuration dictionary (optional, for future extensibility).
    
    Returns:
        A dictionary with paths and checksums.
    """
    logger.info(f"Starting feature matrix generation from {input_csv_path}")
    
    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"Input file not found: {input_csv_path}")
    
    # Load data
    df = pd.read_csv(input_csv_path)
    logger.info(f"Loaded {len(df)} rows from {input_csv_path}")
    
    # Identify feature columns (assuming they are prefixed with 'feat_' or are numeric and not target)
    # Based on T021/T023, we expect numeric feature columns.
    # We'll select all numeric columns except the target if present.
    # Common targets in this project: 'yield_pct', 'success_flag', 'reaction_type'
    exclude_cols = {'yield_pct', 'success_flag', 'reaction_type', 'smiles_reactants', 'smiles_products'}
    feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the input CSV.")
    
    logger.info(f"Selected {len(feature_cols)} feature columns: {feature_cols[:10]}...")
    
    feature_df = df[feature_cols].copy()
    
    # Handle missing values (simple imputation with mean for now, as per T023 logic expectation)
    if feature_df.isnull().any().any():
        logger.warning("Missing values detected in feature matrix. Imputing with mean.")
        feature_df = feature_df.fillna(feature_df.mean())
    
    # Save to Parquet
    checksum_path = output_parquet_path + ".checksum"
    saved_path, checksum = save_feature_matrix(
        feature_df, 
        output_parquet_path, 
        checksum_path
    )
    
    # Register artifact
    artifact_info = {
        "path": saved_path,
        "checksum": checksum,
        "type": "feature_matrix",
        "created_at": datetime.now().isoformat(),
        "source": input_csv_path,
        "feature_count": len(feature_cols),
        "row_count": len(feature_df)
    }
    
    register_artifact(artifact_info)
    logger.info(f"Feature matrix artifact registered: {artifact_info}")
    
    return {
        "output_path": saved_path,
        "checksum": checksum,
        "checksum_path": checksum_path,
        "feature_count": len(feature_cols),
        "row_count": len(feature_df)
    }

def main():
    """
    Main entry point for the preprocessing and feature matrix saving script.
    """
    setup_logger()
    logger.info("Starting T024: Save feature matrix to Parquet")
    
    config = load_config()
    input_csv = config.get("paths", {}).get("filtered_reactions", "data/processed/filtered_reactions.csv")
    output_parquet = config.get("paths", {}).get("feature_matrix", "data/processed/feature_matrix.parquet")
    
    try:
        result = preprocess_and_save_features(input_csv, output_parquet, config)
        logger.info(f"T024 completed successfully. Output: {result}")
    except Exception as e:
        logger.error(f"T024 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
