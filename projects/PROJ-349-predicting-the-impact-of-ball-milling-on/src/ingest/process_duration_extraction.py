"""
T016e: Process Duration Extraction.

Extracts 'process_duration' from source data.
If missing, sets to NaN to allow T016a (Imputation) to handle it.
"""
import logging
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)

def extract_process_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures 'process_duration' column exists.
    
    - If column exists, uses it.
    - If column missing, creates it with NaN.
    - If values are missing in the column, leaves them as NaN.
    
    Args:
        df: Input dataframe.
        
    Returns:
        DataFrame with 'process_duration' column ensured.
    """
    if 'process_duration' not in df.columns:
        logger.warning("'process_duration' column not found. Creating with NaN.")
        df['process_duration'] = float('nan')
    else:
        logger.info("'process_duration' column found. Checking for missing values.")
        missing_count = df['process_duration'].isna().sum()
        if missing_count > 0:
            logger.warning(f"Found {missing_count} missing values in 'process_duration'. Leaving as NaN for imputation.")
        
    return df
