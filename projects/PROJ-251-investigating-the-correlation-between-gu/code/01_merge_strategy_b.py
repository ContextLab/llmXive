import os
import sys
import logging
import pandas as pd
from pathlib import Path
import psutil
from typing import Tuple, Optional, List, Dict, Any

# Import from local utils to ensure consistent config access
# The API surface lists these in utils.config
from utils.config import (
    get_lod_value,
    get_use_synthetic_data,
    get_min_sample_size,
    get_processed_path,
    get_raw_path,
    get_results_path
)
from utils.logging_config import get_logger, log_error_context, log_exclusion_count

logger = get_logger(__name__)

class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass

class InsufficientSampleSizeError(Exception):
    """Raised when the dataset size is below the minimum required."""
    pass

def estimate_memory_footprint(df: pd.DataFrame) -> float:
    """Estimate memory usage of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def handle_lod_titers(df: pd.DataFrame, lod_value: float) -> pd.DataFrame:
    """
    Handle Limit of Detection (LOD) for titer columns.
    
    1. Ensure titer columns are numeric.
    2. Impute 'ND', 'N/A', or empty strings as 0.5 * lod_value.
    3. Raise ConfigurationError if lod_value is not set.
    """
    if lod_value is None:
        raise ConfigurationError(
            "LOD_VALUE must be explicitly set in config. No default allowed."
        )
    
    titer_cols = ['titer_baseline', 'titer_post']
    # Ensure columns exist
    for col in titer_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in dataset.")

    impute_val = 0.5 * lod_value
    
    for col in titer_cols:
        # Convert to numeric, coercing errors to NaN
        original = df[col].copy()
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Identify non-numeric placeholders that became NaN but were originally strings like 'ND'
        # We check the original series for these specific string values
        mask_nd = original.isna() & (
            (original.astype(str).str.strip().str.upper().isin(['ND', 'N/A', 'NA', '']))
        )
        
        # Impute the identified placeholders
        if mask_nd.any():
            logger.info(f"Imputing {mask_nd.sum()} non-numeric LOD placeholders in '{col}' as {impute_val}")
            df.loc[mask_nd, col] = impute_val
        
        # Also handle explicit string 'ND' if it survived (though to_numeric usually catches it)
        # If there are still NaNs now, they are true missing values which we will filter later.
        # The prompt says: "Impute 'ND' or '' values as 0.5 * config.LOD_VALUE".
        # It also says: "Filter out subjects where titer_baseline OR titer_post is truly missing (NaN/Null)".
        # So we only impute the specific LOD markers, then filter remaining NaNs.

    return df

def merge_otu_serology(otu_path: Path, sero_path: Path) -> pd.DataFrame:
    """Merge OTU table and Serology metadata on subject_id."""
    logger.info(f"Merging OTU table: {otu_path} and Serology: {sero_path}")
    
    if not otu_path.exists():
        raise FileNotFoundError(f"OTU table not found at {otu_path}")
    if not sero_path.exists():
        raise FileNotFoundError(f"Serology file not found at {sero_path}")

    df_otu = pd.read_csv(otu_path)
    df_sero = pd.read_csv(sero_path)

    # Ensure subject_id is string for robust merging
    if 'subject_id' in df_otu.columns:
        df_otu['subject_id'] = df_otu['subject_id'].astype(str)
    if 'subject_id' in df_sero.columns:
        df_sero['subject_id'] = df_sero['subject_id'].astype(str)

    merged = pd.merge(
        df_otu,
        df_sero,
        on='subject_id',
        how='inner'
    )
    
    logger.info(f"Merge complete. Rows before filtering: {len(merged)}")
    return merged

def filter_complete_records(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Filter out subjects where titer_baseline OR titer_post is truly missing (NaN).
    '0' abundance is valid, but NaN in titers is not.
    """
    initial_count = len(df)
    required_titer_cols = ['titer_baseline', 'titer_post']
    
    # Check if columns exist
    missing_cols = [c for c in required_titer_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Filter rows where titers are NaN
    mask = df[required_titer_cols].notna().all(axis=1)
    filtered_df = df[mask].copy()
    
    excluded_count = initial_count - len(filtered_df)
    if excluded_count > 0:
        log_exclusion_count("Filter Complete Records", "NaN Titers", excluded_count)
        logger.info(f"Excluded {excluded_count} subjects with missing titer values.")
    
    return filtered_df, excluded_count

def validate_minimum_sample_size(df: pd.DataFrame, use_synthetic: bool) -> None:
    """
    Validate sample size.
    If N < 50 AND real data (not synthetic), raise InsufficientSampleSizeError
    and write error artifacts.
    """
    n = len(df)
    min_n = get_min_sample_size() # Default 50 per spec
    
    if n < min_n and not use_synthetic:
        # Write error artifacts
        results_dir = get_results_path()
        results_dir.mkdir(parents=True, exist_ok=True)
        
        error_msg = f"Insufficient sample size (N = {n}) in final dataset. Minimum required: {min_n}."
        
        # Write sampling_error.json
        error_file = results_dir / "sampling_error.json"
        error_content = {
            "error_type": "InsufficientSampleSize",
            "count": n,
            "message": error_msg
        }
        import json
        with open(error_file, 'w') as f:
            json.dump(error_content, f, indent=2)
        
        # Write error_log.txt
        log_file = results_dir / "error_log.txt"
        with open(log_file, 'a') as f:
            f.write(f"[{pd.Timestamp.now()}] {error_msg}\n")
        
        logger.error(error_msg)
        raise InsufficientSampleSizeError(error_msg)
    
    logger.info(f"Sample size validation passed: N={n}")

def main():
    """Main entry point for T011d: Merge Microbiome and Serology."""
    logger.info("Starting T011d: Merge Microbiome and Serology")
    
    # 1. Determine input paths based on config
    use_synthetic = get_use_synthetic_data()
    raw_dir = get_raw_path()
    processed_dir = get_processed_path()
    
    if use_synthetic:
        otu_path = raw_dir / "synthetic_otutable.csv"
        sero_path = raw_dir / "synthetic_serology.csv"
        logger.info("Using synthetic data sources.")
    else:
        otu_path = raw_dir / "otutable.csv"
        sero_path = raw_dir / "serology.csv"
        logger.info("Using real data sources.")
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Load LOD Value
    lod_value = get_lod_value()
    if lod_value is None:
        # This should be caught by handle_lod_titers, but fail early if config is totally broken
        logger.critical("LOD_VALUE is not set in config.")
        raise ConfigurationError("LOD_VALUE must be explicitly set in config.")
    
    try:
        # 3. Merge
        merged_df = merge_otu_serology(otu_path, sero_path)
        
        # 4. LOD Handling (Impute specific markers)
        # Note: This converts 'ND' etc to numeric. True NaNs remain.
        merged_df = handle_lod_titers(merged_df, lod_value)
        
        # 5. Filter out truly missing titers (NaN)
        filtered_df, _ = filter_complete_records(merged_df)
        
        # 6. Microbiome Completeness Check (Optional but good practice)
        # The spec says: "Verify that for retained subjects, microbiome taxon columns are not truly missing (NaN)"
        # Identify taxon columns (everything except subject_id and titers)
        non_taxa_cols = ['subject_id', 'titer_baseline', 'titer_post']
        taxon_cols = [c for c in filtered_df.columns if c not in non_taxa_cols]
        
        if taxon_cols:
            # Check for NaN in taxon columns
            nano_mask = filtered_df[taxon_cols].isna().any(axis=1)
            if nano_mask.any():
                count_nan = nano_mask.sum()
                log_exclusion_count("Filter Microbiome Completeness", "NaN Taxa", count_nan)
                logger.warning(f"Excluding {count_nan} subjects with missing microbiome data.")
                filtered_df = filtered_df[~nano_mask]
        
        # 7. Validate Sample Size
        validate_minimum_sample_size(filtered_df, use_synthetic)
        
        # 8. Write Output
        output_path = processed_dir / "cleared.csv"
        filtered_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote merged dataset to {output_path} with {len(filtered_df)} rows.")
        
        # Log final stats
        log_sample_size(len(filtered_df))
        
    except InsufficientSampleSizeError:
        # Re-raise to halt execution as per spec
        raise
    except Exception as e:
        log_error_context(e)
        raise

if __name__ == "__main__":
    main()
