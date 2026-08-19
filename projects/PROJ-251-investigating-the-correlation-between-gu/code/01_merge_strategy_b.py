import os
import sys
import logging
import pandas as pd
from pathlib import Path
import psutil

from utils.config import get_raw_path, get_processed_path, get_use_synthetic_data, get_min_sample_size
from utils.logging_config import get_logger, log_exclusion_count, log_sample_size, log_error_context

logger = get_logger(__name__)

class InsufficientSampleSizeError(Exception):
    """Raised when the filtered dataset has fewer subjects than the minimum required."""
    pass

def estimate_memory_footprint(df: pd.DataFrame) -> float:
    """Estimate memory footprint of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def merge_otu_serology(otu_path: Path, serology_path: Path) -> pd.DataFrame:
    """
    Merge OTU table and serology metadata on subject_id.
    Filters out rows where titer_baseline or titer_post are truly missing (NaN).
    Keeps '0' or 'ND' (if parsed as string) values as they are valid.
    """
    logger.info(f"Loading OTU table from: {otu_path}")
    otu_df = pd.read_csv(otu_path)
    
    logger.info(f"Loading serology metadata from: {serology_path}")
    sero_df = pd.read_csv(serology_path)

    # Ensure subject_id is string for consistent merging
    otu_df['subject_id'] = otu_df['subject_id'].astype(str)
    sero_df['subject_id'] = sero_df['subject_id'].astype(str)

    # Merge on subject_id
    merged = pd.merge(otu_df, sero_df, on='subject_id', how='inner')
    
    initial_count = len(merged)
    logger.info(f"Merged dataset size: {initial_count} subjects")

    # Filter out subjects where titer_baseline OR titer_post is truly NaN
    # We check for pd.isna() which catches NaN, None, but NOT '0' or 'ND' (strings)
    # If 'ND' was converted to NaN by read_csv, we need to handle it, 
    # but standard CSV loading keeps 'ND' as string unless na_values is specified.
    # Assuming standard CSV where 'ND' is a string or 0 is a number.
    
    # Check for NaN specifically
    mask_baseline_na = merged['titer_baseline'].isna()
    mask_post_na = merged['titer_post'].isna()
    mask_invalid = mask_baseline_na | mask_post_na

    invalid_count = mask_invalid.sum()
    if invalid_count > 0:
        logger.warning(f"Removing {invalid_count} subjects with missing titer values (NaN).")
        log_exclusion_count("missing_titer_nan", invalid_count)
    
    merged = merged[~mask_invalid]
    
    final_count = len(merged)
    logger.info(f"Dataset size after titer filtering: {final_count} subjects")

    return merged

def main():
    """
    Main entry point for T011d: Merge Microbiome and Serology.
    Handles both real data (T011a) and synthetic data (T011b) paths.
    """
    use_synthetic = get_use_synthetic_data()
    min_samples = get_min_sample_size()
    
    raw_path = get_raw_path()
    processed_path = get_processed_path()

    # Determine input files based on synthetic flag
    if use_synthetic:
        otu_file = raw_path / "synthetic_otutable.csv"
        sero_file = raw_path / "synthetic_serology.csv"
        source_type = "synthetic"
    else:
        otu_file = raw_path / "otutable.csv"
        sero_file = raw_path / "serology.csv"
        source_type = "real"

    # Verify input files exist
    if not otu_file.exists():
        error_msg = f"Input OTU file not found: {otu_file}"
        logger.error(error_msg)
        log_error_context("T011d", error_msg)
        sys.exit(1)
    
    if not sero_file.exists():
        error_msg = f"Input Serology file not found: {sero_file}"
        logger.error(error_msg)
        log_error_context("T011d", error_msg)
        sys.exit(1)

    try:
        # Perform merge and filter
        merged_df = merge_otu_serology(otu_file, sero_file)
        
        # Check sample size
        final_n = len(merged_df)
        log_sample_size(final_n)
        
        if final_n < min_samples and not use_synthetic:
            error_msg = f"Insufficient sample size (N={final_n} < {min_samples}) in final dataset for real data."
            logger.error(error_msg)
            log_exclusion_count("insufficient_sample_size", 1)
            
            # Log to error log file specifically as requested
            error_log_path = processed_path.parent / "results" / "error_log.txt"
            error_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(error_log_path, 'a') as f:
                f.write(f"{datetime.now()}: {error_msg}\n")
            
            raise InsufficientSampleSizeError(error_msg)
        
        if use_synthetic:
            logger.info(f"Synthetic data used. Sample size N={final_n}. Proceeding.")
        else:
            logger.info(f"Real data used. Sample size N={final_n}. Proceeding.")

        # Ensure output directory exists
        processed_path.mkdir(parents=True, exist_ok=True)
        output_file = processed_path / "cleared_with_diversity.csv"

        # Write output
        merged_df.to_csv(output_file, index=False)
        logger.info(f"Successfully wrote merged dataset to: {output_file}")
        
        # Log memory usage
        mem_mb = estimate_memory_footprint(merged_df)
        logger.info(f"Final dataset memory footprint: {mem_mb:.2f} MB")

    except InsufficientSampleSizeError:
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        log_error_context("T011d", str(e))
        sys.exit(1)

if __name__ == "__main__":
    from datetime import datetime
    main()
