import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import yaml

# Configure logging to output to state/pipeline.log as per T005
LOG_PATH = Path("state/pipeline.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import from config to ensure paths are consistent
from config import ensure_directories, get_config_summary

def load_rsa_metrics(filepath: str = "data/derived/rsametrics.csv") -> pd.DataFrame:
    """
    Load RSA metrics from the derived CSV file.
    Validates that the file exists and contains required columns.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"RSA metrics file not found at {filepath}. Run T013/T015 first.")
    
    df = pd.read_csv(filepath)
    required_cols = ['species_id', 'depth', 'branching_density', 'surface_area']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"RSA metrics missing required columns: {missing}")
    
    logger.info(f"Loaded RSA metrics: {len(df)} rows, {len(df.columns)} columns.")
    return df

def load_physiological_data(filepath: str = "data/raw/try_traits.csv") -> pd.DataFrame:
    """
    Load physiological trait data from the raw CSV file.
    Validates that the file exists and contains required columns.
    """
    path = Path(filepath)
    if not path.exists():
        # Try alternative path if standard one is missing (common in some pipeline runs)
        alt_path = Path("data/derived/try_traits.csv")
        if alt_path.exists():
            filepath = str(alt_path)
            path = alt_path
        else:
            raise FileNotFoundError(f"Physiological traits file not found at {filepath}. Run T020 first.")
    
    df = pd.read_csv(filepath)
    # Ensure species_id is the join key and exists
    if 'species_id' not in df.columns:
        # Check for common alternatives
        if 'species' in df.columns:
            df = df.rename(columns={'species': 'species_id'})
        else:
            raise ValueError("Physiological traits file must contain 'species_id' or 'species' column.")
    
    logger.info(f"Loaded physiological data: {len(df)} rows, {len(df.columns)} columns.")
    return df

def merge_datasets(
    rsa_df: pd.DataFrame, 
    physio_df: pd.DataFrame,
    output_path: str = "data/derived/merged_data.csv"
) -> pd.DataFrame:
    """
    Merge RSA metrics with physiological data on species_id.
    Performs species-level stratification checks to prevent duplicate species entries
    that could bias GroupKFold cross-validation.
    
    Logic:
    1. Ensure species_id is unique in both datasets before merge to avoid Cartesian products.
       If duplicates exist in the source data, we aggregate them (mean) to enforce 1:1 mapping
       per species for the regression analysis, or drop duplicates if aggregation is inappropriate.
       Here we aggregate numeric columns by mean to preserve species-level representation.
    2. Perform inner join on 'species_id'.
    3. Validate sample size and species uniqueness in the result.
    """
    logger.info("Starting data merge with species-level stratification.")
    
    # Ensure species_id is the key
    rsa_df = rsa_df.copy()
    physio_df = physio_df.copy()
    
    # Normalize species_id column names if necessary
    if 'species' in rsa_df.columns and 'species_id' not in rsa_df.columns:
        rsa_df = rsa_df.rename(columns={'species': 'species_id'})
    if 'species' in physio_df.columns and 'species_id' not in physio_df.columns:
        physio_df = physio_df.rename(columns={'species': 'species_id'})
    
    # Check for duplicates in RSA metrics per species
    rsa_dupes = rsa_df[rsa_df.duplicated(subset=['species_id'], keep=False)]
    if not rsa_dupes.empty:
        logger.warning(f"Found {len(rsa_dupes)} duplicate species entries in RSA metrics. Aggregating by mean.")
        # Aggregate numeric columns by mean, keeping the first species_id
        numeric_cols = rsa_df.select_dtypes(include=['float64', 'int64']).columns
        rsa_df = rsa_df.groupby('species_id')[numeric_cols].mean().reset_index()
    
    # Check for duplicates in Physiological data per species
    physio_dupes = physio_df[physio_df.duplicated(subset=['species_id'], keep=False)]
    if not physio_dupes.empty:
        logger.warning(f"Found {len(physio_dupes)} duplicate species entries in physiological data. Aggregating by mean.")
        numeric_cols = physio_df.select_dtypes(include=['float64', 'int64']).columns
        physio_df = physio_df.groupby('species_id')[numeric_cols].mean().reset_index()
    
    # Perform the merge (Inner join to keep only species present in both)
    merged_df = pd.merge(rsa_df, physio_df, on='species_id', how='inner')
    
    logger.info(f"Merged dataset shape: {merged_df.shape}")
    
    # Validate species uniqueness in the result (Critical for GroupKFold)
    if merged_df.duplicated(subset=['species_id']).any():
        raise ValueError("CRITICAL: Duplicate species entries found in merged dataset. This will bias GroupKFold.")
    
    # Save to output
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Merged data saved to {output_path}")
    
    return merged_df

def validate_sample_size(df: pd.DataFrame, min_n: int = 55) -> bool:
    """
    Validate that the merged dataset has sufficient sample size for power analysis.
    Returns True if N >= min_n, otherwise raises a critical error.
    """
    n = len(df)
    logger.info(f"Validating sample size: N={n} (Minimum required: {min_n})")
    
    if n < min_n:
        error_msg = f"Insufficient species after merge (N={n} < {min_n}). Pipeline halted per power analysis requirements."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"Sample size validation passed (N={n}).")
    return True

def main():
    """
    Main entry point for the merge data task.
    Orchestrates loading, merging, stratification validation, and sample size checks.
    """
    ensure_directories()
    
    try:
        # Load data
        rsa_df = load_rsa_metrics()
        physio_df = load_physiological_data()
        
        # Merge with stratification logic
        merged_df = merge_datasets(rsa_df, physio_df)
        
        # Validate sample size
        validate_sample_size(merged_df)
        
        # Generate a summary report for state/
        summary = {
            "task": "merge_data",
            "status": "completed",
            "total_rows": len(merged_df),
            "columns": list(merged_df.columns),
            "species_count": merged_df['species_id'].nunique(),
            "stratification_check": "passed"
        }
        
        state_dir = Path("state")
        state_dir.mkdir(parents=True, exist_ok=True)
        with open(state_dir / "merge_summary.yaml", "w") as f:
            yaml.dump(summary, f)
        
        logger.info("Merge task completed successfully.")
        
    except Exception as e:
        logger.critical(f"Merge task failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
