import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from src.utils.logging_config import setup_logging, create_logger
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
MISSING_THRESHOLD = 0.15  # 15%

def calculate_missing_rates(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate missing rate per column."""
    rates = {}
    total_rows = len(df)
    if total_rows == 0:
        return rates
    for col in df.columns:
        null_count = df[col].isna().sum()
        rates[col] = null_count / total_rows
    return rates

def perform_mean_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """Perform mean imputation for columns with <= 15% missing."""
    logger.info("Performing mean imputation...")
    df_imputed = df.copy()
    rates = calculate_missing_rates(df)
    
    for col, rate in rates.items():
        if rate > 0 and rate <= MISSING_THRESHOLD:
            mean_val = df[col].mean()
            if not pd.isna(mean_val):
                df_imputed[col] = df_imputed[col].fillna(mean_val)
                logger.debug(f"Imputed {col} with mean: {mean_val:.4f}")
        elif rate > MISSING_THRESHOLD:
            logger.debug(f"Skipping {col} for mean imputation (rate={rate:.2f} > {MISSING_THRESHOLD})")
    
    return df_imputed

def perform_listwise_deletion(df: pd.DataFrame) -> pd.DataFrame:
    """Perform listwise deletion for columns with > 15% missing."""
    logger.info("Performing listwise deletion...")
    df_clean = df.copy()
    rates = calculate_missing_rates(df)
    
    cols_to_drop = [col for col, rate in rates.items() if rate > MISSING_THRESHOLD]
    if cols_to_drop:
        logger.warning(f"Dropping columns with >15% missing: {cols_to_drop}")
        df_clean = df_clean.drop(columns=cols_to_drop)
    
    # Drop rows with any remaining NaNs in critical columns
    # Assuming critical columns are numeric targets/features
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        df_clean = df_clean.dropna(subset=numeric_cols)
    
    logger.info(f"Listwise deletion complete. Rows remaining: {len(df_clean)}")
    return df_clean

def orchestrate_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Orchestrates imputation strategy per Spec FR-002.
    If any column has > 15% missing, use listwise deletion.
    Else, use mean imputation.
    """
    if df.empty:
        return df
    
    rates = calculate_missing_rates(df)
    max_rate = max(rates.values()) if rates else 0
    
    logger.info(f"Imputation orchestration. Max missing rate: {max_rate:.2f}")
    
    if max_rate > MISSING_THRESHOLD:
        logger.warning(f"Missing rate ({max_rate:.2f}) > {MISSING_THRESHOLD}. Using Listwise Deletion.")
        return perform_listwise_deletion(df)
    else:
        logger.info(f"Missing rate ({max_rate:.2f}) <= {MISSING_THRESHOLD}. Using Mean Imputation.")
        return perform_mean_imputation(df)

def main():
    setup_logging()
    logger.info("Imputation Orchestrator Main Entry")
    # This is a utility function called by the pipeline
    return 0

if __name__ == "__main__":
    sys.exit(main())