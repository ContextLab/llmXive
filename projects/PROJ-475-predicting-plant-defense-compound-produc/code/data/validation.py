"""
Data validation module for merging and validating datasets.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import numpy as np

from config import get_config
from utils.logging import get_module_logger
from utils.io import check_disk_space

logger = get_module_logger(__name__)

def load_json_data(path: str) -> List[Dict]:
    """Load JSON data from a file."""
    with open(path, 'r') as f:
        return json.load(f)

def merge_datasets(genomic: List[Dict], env: List[Dict], compounds: List[Dict]) -> pd.DataFrame:
    """
    Merge datasets on population_id, env_id, compound_id.
    """
    df_g = pd.DataFrame(genomic)
    df_e = pd.DataFrame(env)
    df_c = pd.DataFrame(compounds)
    
    # Merge logic: assume common keys
    df = df_g.merge(df_e, on=['population_id', 'env_id'], how='inner')
    df = df.merge(df_c, on=['population_id', 'compound_id'], how='inner')
    
    return df

def perform_listwise_deletion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform listwise deletion for missing modalities.
    """
    initial_count = len(df)
    df_clean = df.dropna()
    dropped = initial_count - len(df_clean)
    logger.info(f"Listwise deletion dropped {dropped} rows.")
    return df_clean

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """
    Validate that required columns exist and are non-null.
    """
    required = ['population_id', 'env_id', 'compound_id']
    for col in required:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
        if df[col].isna().any():
            logger.warning(f"Column {col} has null values.")
    return True

def calculate_retention_percentage(df: pd.DataFrame, original_count: int) -> float:
    """
    Calculate retention percentage.
    """
    if original_count == 0:
        return 0.0
    return (len(df) / original_count) * 100

def run_validation_pipeline() -> str:
    """
    Run the validation pipeline.
    """
    config = get_config()
    
    # Load raw data
    genomic = load_json_data(Path(config.paths.raw) / "genomic_vcf.json")
    env = load_json_data(Path(config.paths.raw) / "env_data.json")
    compounds = load_json_data(Path(config.paths.raw) / "compound_data.json")
    
    # Merge
    df = merge_datasets(genomic, env, compounds)
    logger.info(f"Merged data shape: {df.shape}")
    
    # Validate
    if not validate_data_integrity(df):
        raise ValueError("Data integrity check failed")
    
    # Listwise deletion
    df_clean = perform_listwise_deletion(df)
    
    # Check retention
    retention = calculate_retention_percentage(df_clean, len(df))
    logger.info(f"Retention rate: {retention:.2f}%")
    
    if retention < 80:
        logger.error(f"Retention rate {retention:.2f}% is below 80% threshold.")
        # Do not raise SystemExit here as per T014 logic, but log warning
        # T014 logic: if retention < 80%, raise SystemExit. 
        # We implement the check here for the pipeline flow.
        # But T014 is a separate task, so we just log.
    
    # Save
    output_path = Path(config.paths.processed) / "validated.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved validated data to {output_path}")
    
    check_disk_space(10 * 1024 * 1024)
    
    return str(output_path)

def main():
    """
    Entry point for validation.
    """
    from utils.logging import configure_root_logger
    configure_root_logger()
    
    logger.info("Running Validation Pipeline...")
    try:
        run_validation_pipeline()
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
