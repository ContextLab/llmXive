"""
Task T021: Log-Transform Titers & LOD Handling.

This script reads the output of the Shannon Diversity calculation (cleared_shannon.csv),
handles Limit of Detection (LOD) imputation for titer values, and applies a log10
transformation to create titer_pre_log and titer_post_log columns.

Input: data/processed/cleared_shannon.csv
Output: data/processed/cleared_shannon_log.csv
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_lod_value, get_env_var
from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

def load_cleared_data(input_path: Path) -> pd.DataFrame:
    """Load the cleared dataset with Shannon diversity."""
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    required_cols = ['subject_id', 'titer_baseline', 'titer_post', 'shannon_diversity']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def apply_lod_imputation_and_log_transform(df: pd.DataFrame, lod_value: float) -> pd.DataFrame:
    """
    Apply LOD imputation and log10 transformation to titers.
    
    Logic:
    1. Ensure titers are numeric.
    2. Impute values <= 0 or NaN with 0.5 * LOD (if they represent non-detects).
       Note: The task description implies handling 'ND' or empty strings as 0.5*LOD.
       Since we are reading from CSV, 'ND' might be read as NaN or string.
       We treat <= 0 values as candidates for imputation if they represent non-detects.
       However, strictly following the task: "Impute 'ND' or '' values as 0.5 * config.LOD_VALUE".
       If the data is already numeric (from T011d), we assume 0 or negative values are the 
       representation of non-detects or need imputation. 
       
       Strategy:
       - Convert to numeric, coercing errors to NaN.
       - Fill NaN with 0.5 * LOD.
       - Fill 0 with 0.5 * LOD (assuming 0 implies non-detect in this context, 
         though biological 0 is impossible for log transform).
       - Apply log10.
    """
    logger.info(f"Applying LOD handling with LOD_VALUE={lod_value}")
    
    df = df.copy()
    
    # Ensure titer columns are numeric
    for col in ['titer_baseline', 'titer_post']:
        if col in df.columns:
            original_dtype = df[col].dtype
            df[col] = pd.to_numeric(df[col], errors='coerce')
            logger.debug(f"Converted {col} from {original_dtype} to numeric. NaNs introduced: {df[col].isna().sum()}")
    
    # Imputation Strategy:
    # The task states: "Impute 'ND' or '' values as 0.5 * config.LOD_VALUE".
    # In a numeric CSV, these usually appear as NaN or 0.
    # We will replace NaN and 0 (or values <= 0) with 0.5 * LOD to allow log transformation.
    impute_value = 0.5 * lod_value
    
    for col in ['titer_baseline', 'titer_post']:
        if col in df.columns:
            # Count non-detects (NaN or <= 0)
            non_detects = df[col].isna() | (df[col] <= 0)
            count = non_detects.sum()
            if count > 0:
                logger.info(f"Imputing {count} non-detect/zero values in {col} with {impute_value}")
                df.loc[non_detects, col] = impute_value
            else:
                logger.info(f"No non-detect/zero values found in {col} to impute.")
    
    # Apply Log10 Transform
    logger.info("Applying log10 transformation to titers")
    df['titer_pre_log'] = np.log10(df['titer_baseline'])
    df['titer_post_log'] = np.log10(df['titer_post'])
    
    # Verify no -inf or NaN in log columns
    if df['titer_pre_log'].isna().any() or (df['titer_pre_log'] == -np.inf).any():
        logger.warning("Found invalid log values (NaN or -inf) in titer_pre_log after transformation.")
    if df['titer_post_log'].isna().any() or (df['titer_post_log'] == -np.inf).any():
        logger.warning("Found invalid log values (NaN or -inf) in titer_post_log after transformation.")
    
    return df

def write_updated_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Write the updated dataset to CSV."""
    logger.info(f"Writing updated dataset to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")

def run_log_titer_pipeline(input_path: Optional[Path] = None, 
                           output_path: Optional[Path] = None) -> Path:
    """Orchestrate the log titer pipeline."""
    # Default paths
    if input_path is None:
        input_path = Path("data/processed/cleared_shannon.csv")
    if output_path is None:
        output_path = Path("data/processed/cleared_shannon_log.csv")
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Get LOD value from config
    lod_value = get_lod_value()
    if lod_value is None:
        raise ConfigurationError("LOD_VALUE must be explicitly set in config. No default allowed.")
    
    logger.info(f"Starting Log Titer Pipeline. Input: {input_path}, Output: {output_path}")
    
    # 1. Load
    df = load_cleared_data(input_path)
    
    # 2. Transform
    df_transformed = apply_lod_imputation_and_log_transform(df, lod_value)
    
    # 3. Write
    write_updated_dataset(df_transformed, output_path)
    
    logger.info("Log Titer Pipeline completed successfully.")
    return output_path

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

def main():
    """Main entry point for the script."""
    try:
        # Ensure environment is loaded
        load_dotenv_file = get_env_var  # Just to trigger config loading if needed
        
        output_file = run_log_titer_pipeline()
        print(f"Pipeline completed. Output written to: {output_file}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
