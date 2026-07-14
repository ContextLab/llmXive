"""
Data Validation and Merging Module.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np

from utils.logging import get_module_logger
from config import get_config

logger = get_module_logger(__name__)

PROCESSED_DIR = Path("data/processed")

def load_json_data(file_path: str) -> Optional[pd.DataFrame]:
    """Loads a JSON file into a DataFrame."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict):
        return pd.DataFrame([data])
    else:
        logger.error(f"Unexpected data format in {file_path}")
        return None

def merge_datasets(genomic: pd.DataFrame, env_data: pd.DataFrame, compound: pd.DataFrame) -> pd.DataFrame:
    """
    Merges genomic, environmental, and compound datasets.
    Performs inner join on population_id, env_id, compound_id.
    """
    # Ensure IDs are strings for consistent merging
    for df in [genomic, env_data, compound]:
        for col in ['population_id', 'env_id', 'compound_id']:
            if col in df.columns:
                df[col] = df[col].astype(str)

    # Merge step-by-step
    merged = genomic.merge(env_data, on=['population_id', 'env_id', 'compound_id'], how='inner')
    merged = merged.merge(compound, on=['population_id', 'env_id', 'compound_id'], how='inner')
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def perform_listwise_deletion(df: pd.DataFrame, required_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Performs listwise deletion (dropping rows with any NaN in specified columns).
    
    Args:
        df: Input DataFrame.
        required_cols: Columns to check for NaN. If None, checks all columns.
        
    Returns:
        Cleaned DataFrame.
    """
    if required_cols is None:
        required_cols = df.columns.tolist()
    
    initial_count = len(df)
    df_clean = df.dropna(subset=required_cols)
    final_count = len(df_clean)
    
    dropped = initial_count - final_count
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows ({dropped/initial_count*100:.2f}%) due to missing values in required columns.")
    else:
        logger.info("No rows dropped due to missing values.")
        
    return df_clean

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """Validates basic data integrity (non-null IDs)."""
    id_cols = ['population_id', 'env_id', 'compound_id']
    for col in id_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
        if df[col].isna().any():
            logger.error(f"Null values found in required column: {col}")
            return False
    return True

def calculate_retention_percentage(original_count: int, final_count: int) -> float:
    """Calculates retention percentage."""
    if original_count == 0:
        return 0.0
    return (final_count / original_count) * 100

def run_validation_pipeline() -> pd.DataFrame:
    """
    Orchestrates the validation pipeline:
    1. Load raw JSONs.
    2. Merge.
    3. Listwise deletion.
    4. Save merged.csv.
    """
    logger.info("Starting validation pipeline (T013/T014).")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    genomic = load_json_data("data/raw/genomic_vcf.json")
    env_data = load_json_data("data/raw/env_data.json")
    compound = load_json_data("data/raw/compound_data.json")

    if genomic is None or env_data is None or compound is None:
        raise FileNotFoundError("Missing required raw data files for validation.")

    # Merge
    merged = merge_datasets(genomic, env_data, compound)
    
    if not validate_data_integrity(merged):
        raise ValueError("Data integrity validation failed.")

    # Listwise deletion
    cleaned = perform_listwise_deletion(merged)
    
    retention = calculate_retention_percentage(len(merged), len(cleaned))
    logger.info(f"Retention percentage: {retention:.2f}%")
    
    if retention < 80:
        logger.error(f"Retention ({retention:.2f}%) is below 80% threshold. Raising SystemExit.")
        # T014 requirement: raise SystemExit if < 80%
        # Note: In a real pipeline, this might be handled by the orchestrator, 
        # but per task spec, we raise here.
        raise SystemExit("E-DATA-INSUFFICIENT: Retention below 80%")

    # Save
    merged_path = PROCESSED_DIR / "merged.csv"
    cleaned.to_csv(merged_path, index=False)
    logger.info(f"Saved merged/cleaned data to {merged_path}")

    return cleaned

def main():
    """Entry point for validation script."""
    from utils.logging import configure_root_logger
    configure_root_logger()
    run_validation_pipeline()

if __name__ == "__main__":
    main()
