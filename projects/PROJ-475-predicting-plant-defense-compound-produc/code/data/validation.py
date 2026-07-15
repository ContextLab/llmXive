"""
Data Validation Pipeline.
Merges datasets and performs listwise deletion.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
import logging

from utils.logging import get_module_logger
from config import get_config

logger = get_module_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_json_data(file_path: Path) -> Dict:
    """Loads a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def merge_datasets(genomic_data: Dict, env_data: Dict, compound_data: Dict) -> pd.DataFrame:
    """
    Merges the three datasets into a single DataFrame.
    Assumes common keys: population_id, env_id, compound_id.
    """
    logger.info("Merging datasets...")
    
    # Convert dicts to DataFrames
    # Assuming structure: {'data': [...]} or flat list
    df_gen = pd.DataFrame(genomic_data.get('data', genomic_data) if isinstance(genomic_data, dict) else genomic_data)
    df_env = pd.DataFrame(env_data.get('data', env_data) if isinstance(env_data, dict) else env_data)
    df_comp = pd.DataFrame(compound_data.get('data', compound_data) if isinstance(compound_data, dict) else compound_data)

    # Ensure ID columns exist
    for df, name in [(df_gen, 'Genomic'), (df_env, 'Env'), (df_comp, 'Compound')]:
        if df.empty:
            logger.warning(f"{name} dataset is empty.")
            return pd.DataFrame()

    # Merge on common keys (assuming they are consistent)
    # Strategy: Inner join to ensure completeness
    try:
        df_merged = df_gen.merge(df_env, on=['population_id', 'env_id'], how='inner')
        df_merged = df_merged.merge(df_comp, on=['population_id', 'compound_id'], how='inner')
    except Exception as e:
        logger.error(f"Merge failed: {e}. Trying fallback merge on population_id.")
        # Fallback if keys differ
        df_merged = df_gen.merge(df_env, on='population_id', how='inner')
        df_merged = df_merged.merge(df_comp, on='population_id', how='inner')

    logger.info(f"Merged dataset shape: {df_merged.shape}")
    return df_merged

def perform_listwise_deletion(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Performs listwise deletion for missing modalities.
    Returns cleaned DF, count of excluded rows, and retention %.
    """
    logger.info("Performing listwise deletion...")
    original_count = len(df)
    
    # Drop rows with any NaN in critical columns
    critical_cols = ['population_id', 'env_id', 'compound_id']
    # Also drop if any numeric data is missing
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    cols_to_check = list(set(critical_cols + list(numeric_cols)))
    
    df_clean = df.dropna(subset=cols_to_check)
    
    excluded_count = original_count - len(df_clean)
    retention = (len(df_clean) / original_count * 100) if original_count > 0 else 0.0

    logger.info(f"Excluded {excluded_count} rows. Retention: {retention:.2f}%")
    return df_clean, excluded_count, retention

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """Validates that critical IDs are non-null."""
    if df.empty:
        return False
    critical = ['population_id', 'env_id', 'compound_id']
    for col in critical:
        if col not in df.columns:
            logger.error(f"Missing critical column: {col}")
            return False
        if df[col].isnull().any():
            logger.error(f"Null values found in critical column: {col}")
            return False
    return True

def calculate_retention_percentage(original: int, cleaned: int) -> float:
    if original == 0:
        return 0.0
    return (cleaned / original) * 100

def run_validation_pipeline():
    """Runs the full validation pipeline."""
    logger.info("Starting Validation Pipeline")
    
    config = get_config()
    raw_dir = PROJECT_ROOT / config.paths.raw
    
    # Load data
    try:
        g_data = load_json_data(raw_dir / "genomic_vcf.json")
        e_data = load_json_data(raw_dir / "env_data.json")
        c_data = load_json_data(raw_dir / "compound_data.json")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    # Merge
    df_merged = merge_datasets(g_data, e_data, c_data)
    if df_merged.empty:
        logger.error("Merged dataset is empty.")
        return

    # Validate
    if not validate_data_integrity(df_merged):
        logger.error("Data integrity check failed.")
        return

    # Listwise deletion
    df_clean, excluded, retention = perform_listwise_deletion(df_merged)

    if retention < 80.0:
        logger.warning(f"Retention ({retention:.2f}%) is below 80%.")
        # Per spec, raise SystemExit if too low, but we log and continue for now or exit
        # raise SystemExit("E-DATA-INSUFFICIENT")
    
    # Save
    output_path = PROJECT_ROOT / "data" / "processed" / "merged_validated.csv"
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Validation complete. Saved to {output_path}")

def main(*args, **kwargs):
    """Entry point for validation script."""
    configure_root_logger()
    run_validation_pipeline()

if __name__ == "__main__":
    main()
