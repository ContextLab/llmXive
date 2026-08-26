import os
import sys
import logging
import pandas as pd
from pathlib import Path
import psutil
from typing import Tuple, Optional
from utils.logging_config import get_logger, log_error_context
from utils.config import get_min_sample_size, get_use_synthetic_data, get_raw_path, get_processed_path

logger = get_logger(__name__)

class InsufficientSampleSizeError(Exception):
    """Raised when the final merged dataset has fewer subjects than required."""
    pass

def estimate_memory_footprint(df: pd.DataFrame) -> float:
    """Estimates memory usage of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def merge_otu_serology(otu_path: Path, serology_path: Path, min_n: int, use_synthetic: bool) -> pd.DataFrame:
    """
    Merges OTU table and serology metadata on subject_id.
    
    Logic:
    1. Merge datasets on 'subject_id'.
    2. Filter out subjects where titer_baseline OR titer_post is truly missing (NaN/Null).
       Do NOT filter out valid '0' or 'ND' (Not Detected) values unless they are actual NaNs.
    3. Verify microbiome taxon columns are not truly missing (NaN) for retained subjects.
       '0' abundance is valid.
    4. Count subjects (N).
    5. If N < min_n AND use_synthetic is False, raise InsufficientSampleSizeError.
    6. Return the filtered DataFrame.
    """
    logger.info(f"Loading OTU table from: {otu_path}")
    otu_df = pd.read_csv(otu_path)
    
    logger.info(f"Loading serology metadata from: {serology_path}")
    sero_df = pd.read_csv(serology_path)
    
    # Check for required columns
    if 'subject_id' not in otu_df.columns or 'subject_id' not in sero_df.columns:
        raise ValueError("Both datasets must contain 'subject_id' column.")
    
    # Merge on subject_id (inner join to keep only matched subjects)
    merged_df = pd.merge(otu_df, sero_df, on='subject_id', how='inner')
    logger.info(f"Post-merge count: {len(merged_df)} subjects")
    
    # Filter out rows where titer_baseline OR titer_post is NaN (truly missing)
    # We use pd.notna() to keep 0s and other valid values
    initial_count = len(merged_df)
    merged_df = merged_df[pd.notna(merged_df['titer_baseline']) & pd.notna(merged_df['titer_post'])]
    excluded_count = initial_count - len(merged_df)
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} subjects due to missing titer values (NaN).")
    
    # Identify taxon columns (all columns except subject_id and titer columns)
    # Assuming serology columns are strictly 'subject_id', 'titer_baseline', 'titer_post'
    # and potentially 'log_titer' if already processed, but T011d happens before T021 in strict flow?
    # The task description says: Input: otutable.csv, serology.csv.
    # We need to filter out rows where microbiome taxon columns are NaN.
    # Let's assume taxon columns are everything not in the known serology list.
    known_serology_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [col for col in merged_df.columns if col not in known_serology_cols]
    
    # Filter out rows where any taxon column is NaN
    # '0' is valid, only NaN is invalid
    if taxon_cols:
        initial_taxo_count = len(merged_df)
        # Drop rows where any of the taxon columns are NaN
        merged_df = merged_df.dropna(subset=taxon_cols)
        excluded_taxo_count = initial_taxo_count - len(merged_df)
        if excluded_taxo_count > 0:
            logger.info(f"Excluded {excluded_taxo_count} subjects due to missing microbiome data (NaN).")
    
    final_n = len(merged_df)
    logger.info(f"Final subject count after filtering: {final_n}")
    
    if final_n < min_n:
        if not use_synthetic:
            error_msg = f"Insufficient sample size (N < {min_n}) in final dataset. Found {final_n}."
            logger.error(error_msg)
            # Log to error log file as requested
            error_log_path = Path(get_raw_path().parent) / "results" / "error_log.txt"
            error_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(error_log_path, 'a') as f:
                f.write(f"{error_msg}\n")
            raise InsufficientSampleSizeError(error_msg)
        else:
            logger.warning(f"Synthetic data mode: Sample size {final_n} is below {min_n}, but proceeding.")
    
    return merged_df

def main():
    """
    Main entry point for T011d: Merge Microbiome and Serology.
    Determines input files based on config (real vs synthetic) and writes output.
    """
    try:
        raw_path = Path(get_raw_path())
        processed_path = Path(get_processed_path())
        processed_path.mkdir(parents=True, exist_ok=True)
        
        use_synthetic = get_use_synthetic_data()
        min_n = get_min_sample_size()
        
        if use_synthetic:
            otu_file = raw_path / "synthetic_otutable.csv"
            sero_file = raw_path / "synthetic_serology.csv"
            logger.info("Using synthetic data sources.")
        else:
            otu_file = raw_path / "otutable.csv"
            sero_file = raw_path / "serology.csv"
            logger.info("Using real data sources.")
        
        if not otu_file.exists():
            raise FileNotFoundError(f"OTU table not found: {otu_file}")
        if not sero_file.exists():
            raise FileNotFoundError(f"Serology metadata not found: {sero_file}")
        
        merged_df = merge_otu_serology(otu_file, sero_file, min_n, use_synthetic)
        
        output_file = processed_path / "cleared_with_diversity.csv"
        merged_df.to_csv(output_file, index=False)
        logger.info(f"Successfully wrote merged dataset to: {output_file}")
        logger.info(f"Final dataset shape: {merged_df.shape}")
        
    except InsufficientSampleSizeError as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        log_error_context(logger, e)
        sys.exit(1)

if __name__ == "__main__":
    main()
